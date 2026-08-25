from __future__ import annotations

from integrations_page import scan_all_mail


if __name__ == "__main__":
    items = scan_all_mail()
    print(f"Integration mail scan completed; checklist_items={len(items)}")
