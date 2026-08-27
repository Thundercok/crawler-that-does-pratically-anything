"""
rat.cli — Command-line interface with rich terminal formatting.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from rat.config import config
from rat.crawler.db import Database
from rat.crawler.indexer import Indexer
from rat.engine.hybrid_search import SearchEngine
from rat.ui.preview_panel import open_file_default, reveal_in_finder

console = Console()


def cmd_index(directories: Optional[List[str]] = None) -> None:
    """Index files from directories."""
    target_dirs = directories if directories else config.indexed_directories
    console.print(Panel.fit(f"[bold cyan]🐀 'rat' File Indexer[/bold cyan]\nQuét các thư mục: {', '.join(target_dirs)}", border_style="cyan"))

    indexer = Indexer()
    files = indexer.discover_files(target_dirs)
    total = len(files)

    if total == 0:
        console.print("[yellow]Không tìm thấy tệp nào phù hợp để lập chỉ mục.[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Đang lập chỉ mục {total} tệp...", total=total)

        def on_progress(done: int, tot: int, filename: str) -> None:
            progress.update(task, completed=done, description=f"Quét: [green]{filename[:25]}[/green]")

        indexed, _ = indexer.run_full_index(directories=target_dirs, progress_callback=on_progress)

    db = Database(config.db_path)
    stats = db.get_stats()
    size_mb = stats["total_size_bytes"] / (1024 * 1024)
    console.print(f"[bold green]✓ Hoàn tất![/bold green] Đã cập nhật {indexed}/{total} tệp. Tổng kho lưu trữ: {stats['total_files']} tệp (~{size_mb:.1f} MB).")


def cmd_search(query: str, limit: int = 10, open_first: bool = False, reveal_first: bool = False) -> None:
    """Search files using natural language query."""
    engine = SearchEngine()
    response = engine.search(query, limit=limit)

    results = response["results"]
    parsed = response["parsed_context"]
    latency = response["latency_ms"]
    sparse_count = response.get("sparse_count", 0)
    dense_count = response.get("dense_count", 0)
    hypo_text = response.get("hypo_text")

    # Filter description banner
    filter_tags = []
    if parsed.get("file_type_desc"):
        filter_tags.append(f"[blue]📁 {parsed['file_type_desc']}[/blue]")
    if parsed.get("time_desc"):
        filter_tags.append(f"[magenta]📅 {parsed['time_desc']}[/magenta]")
    if parsed.get("keywords"):
        filter_tags.append(f"[yellow]🔑 {', '.join(parsed['keywords'])}[/yellow]")

    filter_tags.append(f"[cyan]⚡ FTS5: {sparse_count} | Vectors: {dense_count}[/cyan]")

    header = f"🔍 Truy vấn: [bold white]\"{query}\"[/bold white]"
    if filter_tags:
        header += "  |  " + "  ".join(filter_tags)
    header += f"  (Tìm thấy {len(results)} tệp trong {latency}ms)"

    if hypo_text:
        header += f"\n\n[dim italic]🧠 HyDE Context:[/dim italic] [dim]\"{hypo_text[:160]}...\"[/dim]"

    console.print(Panel(header, title="🐀 True Hybrid Search (RRF + HyDE)", border_style="blue"))

    if not results:
        console.print("[yellow]Không tìm thấy tệp nào khớp với mô tả của bạn. Hãy thử quét lại (`rat index`) hoặc mô tả khác.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("#", style="dim", width=3)
    table.add_column("Tên tệp", style="bold white", width=26)
    table.add_column("Loại", style="cyan", width=6)
    table.add_column("Đã sửa", style="magenta", width=14)
    table.add_column("Lý do khớp (Context Reasoning)", style="green", width=40)
    table.add_column("Độ khớp", style="yellow", justify="right", width=9)

    for idx, item in enumerate(results, 1):
        table.add_row(
            str(idx),
            item.file_name,
            item.file_ext.upper(),
            item.modified_formatted,
            item.explanation,
            f"{int(item.score)}%"
        )

    console.print(table)

    if open_first and results:
        first = results[0]
        console.print(f"[bold green]⚡ Đang mở tệp:[/bold green] {first.file_path}")
        open_file_default(first.file_path)
    elif reveal_first and results:
        first = results[0]
        console.print(f"[bold green]📁 Đang mở trong Finder:[/bold green] {first.file_path}")
        reveal_in_finder(first.file_path)


def cmd_ask(file_query: str, question: str) -> None:
    """Find file and ask the local SLM to answer question about its content."""
    from rat.crawler.extractors import extract_document_content
    from rat.engine.slm import slm_engine

    engine = SearchEngine()
    response = engine.search(file_query, limit=1)
    results = response["results"]

    if not results:
        console.print(f"[yellow]Không tìm thấy file nào khớp với '{file_query}'.[/yellow]")
        return

    top_file = results[0]
    console.print(Panel.fit(
        f"📄 [bold white]{top_file.file_name}[/bold white]\n"
        f"[dim]{top_file.file_path}[/dim]\n"
        f"❓ Câu hỏi: [bold yellow]{question}[/bold yellow]",
        title="🧠 'rat' SLM Document Q&A",
        border_style="blue"
    ))

    with console.status("[bold green]SLM đang phân tích tài liệu và suy luận..."):
        content = extract_document_content(top_file.file_path)
        answer = slm_engine.ask_document(content, question)

    console.print(Panel(answer, title="💡 Câu trả lời từ SLM (Qwen2.5 / Apple Silicon)", border_style="green"))


def cmd_stats() -> None:
    """Print indexing statistics."""
    from rat.engine.slm import slm_engine
    db = Database(config.db_path)
    stats = db.get_stats()
    size_mb = stats["total_size_bytes"] / (1024 * 1024)
    slm_status = "🟢 Hoạt động (qwen2.5:1.5b)" if slm_engine.is_model_installed() else "🟡 Chưa sẵn sàng"

    console.print(Panel.fit(
        f"[bold cyan]🐀 'rat' Search Engine Status[/bold cyan]\n\n"
        f"• Tổng số tệp trong chỉ mục: [bold white]{stats['total_files']}[/bold white]\n"
        f"• Dung lượng nội dung: [bold white]{size_mb:.2f} MB[/bold white]\n"
        f"• Bộ não SLM cục bộ: [bold green]{slm_status}[/bold green]\n"
        f"• Vị trí Database: [dim]{config.db_path}[/dim]\n"
        f"• Các thư mục theo dõi: [green]{', '.join(config.indexed_directories)}[/green]",
        border_style="cyan"
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description="rat — Smart Local File Finder with Context Engineering & SLM")
    subparsers = parser.add_subparsers(dest="command")

    # Index command
    index_parser = subparsers.add_parser("index", help="Scan and index folders")
    index_parser.add_argument("dirs", nargs="*", help="Optional directories to index")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search files with natural language")
    search_parser.add_argument("query", help="Natural language query description")
    search_parser.add_argument("-n", "--limit", type=int, default=10, help="Max results")
    search_parser.add_argument("-o", "--open", action="store_true", help="Open best matching file")
    search_parser.add_argument("-f", "--finder", action="store_true", help="Reveal best match in Finder")

    # Ask SLM command
    ask_parser = subparsers.add_parser("ask", help="Ask local SLM a question about a file")
    ask_parser.add_argument("file_query", help="Query to identify the file")
    ask_parser.add_argument("question", help="Question to ask about the file")

    # Status command
    subparsers.add_parser("status", help="Show index statistics")

    args = parser.parse_args()

    if args.command == "index":
        cmd_index(args.dirs if args.dirs else None)
    elif args.command == "search":
        cmd_search(args.query, limit=args.limit, open_first=args.open, reveal_first=args.finder)
    elif args.command == "ask":
        cmd_ask(args.file_query, args.question)
    elif args.command == "status":
        cmd_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
