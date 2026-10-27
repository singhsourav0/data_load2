import concurrent.futures
import os
import random
import ssl
import threading
import time
from collections import Counter, defaultdict
from urllib import error, request

TARGET_URL = os.getenv("TARGET_URL", "https://appsthilaz.com/")
TOTAL_REQUESTS = int(os.getenv("TOTAL_REQUESTS", "100000"))
MAX_THREADS = int(os.getenv("MAX_THREADS", "500"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
PROGRESS_INTERVAL = int(os.getenv("PROGRESS_INTERVAL", "500"))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

stats_lock = threading.Lock()
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "status_codes": Counter(),
    "latencies": [],
    "errors": defaultdict(int),
}


def fetch_once():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    req = request.Request(TARGET_URL, headers=headers, method="GET")
    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            status = resp.getcode()
            resp.read(2048)
            elapsed = time.perf_counter() - start
            with stats_lock:
                stats["total"] += 1
                total_now = stats["total"]
                stats["status_codes"][status] += 1
                stats["latencies"].append(elapsed)
                if 200 <= status < 400:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"][f"status_{status}"] += 1
            if total_now % PROGRESS_INTERVAL == 0:
                print(f"Progress: {total_now}/{TOTAL_REQUESTS} requests completed")
            return status, elapsed, None
    except error.HTTPError as exc:
        elapsed = time.perf_counter() - start
        with stats_lock:
            stats["total"] += 1
            total_now = stats["total"]
            stats["failed"] += 1
            stats["status_codes"][exc.code] += 1
            stats["latencies"].append(elapsed)
            stats["errors"][f"http_{exc.code}"] += 1
        if total_now % PROGRESS_INTERVAL == 0:
            print(f"Progress: {total_now}/{TOTAL_REQUESTS} requests completed")
        return exc.code, elapsed, str(exc)
    except Exception as exc:
        elapsed = time.perf_counter() - start
        with stats_lock:
            stats["total"] += 1
            total_now = stats["total"]
            stats["failed"] += 1
            stats["latencies"].append(elapsed)
            stats["errors"][str(exc)] += 1
        if total_now % PROGRESS_INTERVAL == 0:
            print(f"Progress: {total_now}/{TOTAL_REQUESTS} requests completed")
        return None, elapsed, str(exc)


def print_summary():
    total = stats["total"]
    success = stats["success"]
    failed = stats["failed"]
    latencies = stats["latencies"]
    avg = sum(latencies) / len(latencies) if latencies else 0
    p95_index = max(0, min(len(latencies) - 1, int(len(latencies) * 0.95)))
    p95 = sorted(latencies)[p95_index] if latencies else 0

    print("\n=== Load Test Summary ===")
    print(f"Target: {TARGET_URL}")
    print(f"Threads: {MAX_THREADS}")
    print(f"Total requested: {TOTAL_REQUESTS}")
    print(f"Total completed: {total}")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Average latency: {avg:.3f}s")
    print(f"P95 latency: {p95:.3f}s")
    print(f"Status codes: {dict(stats['status_codes'])}")
    if stats["errors"]:
        print("Errors:")
        for err, count in stats["errors"].items():
            print(f"  {err}: {count}")


def main():
    print(f"Starting {TOTAL_REQUESTS} requests against {TARGET_URL} using {MAX_THREADS} threads")
    start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
        futures = [pool.submit(fetch_once) for _ in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"Unexpected worker exception: {exc}")

    elapsed = time.perf_counter() - start
    print(f"Run completed in {elapsed:.2f}s")
    print_summary()


if __name__ == "__main__":
    main()
