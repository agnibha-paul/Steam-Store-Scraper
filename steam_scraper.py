import re
import csv
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ''(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

TAG_IDS = {
    "Action": 19,
    "Adventure": 21,
    "RPG": 122,
    "Strategy": 9,
    "Simulation": 599,
    "Casual": 597,
    "Indie": 492,
    "Horror": 1667,
    "Open World": 1695,
    "Multiplayer": 3859,
    "Singleplayer": 4182,
    "Co-op": 1685,
    "Online Co-op": 3843,
    "Local Co-op": 3841,
    "PvP": 1775,
    "Sports": 701,
    "Racing": 699,
    "Puzzle": 1664,
    "Sci-fi": 3942,
    "Fantasy": 1684,
    "Survival": 1662,
    "Shooter": 1774,
    "FPS": 1663,
    "Story Rich": 9983,
    "Atmospheric": 4166,
    "Early Access": 4756,
    "VR": 21978,
    "Free to Play": 113,
    "Anime": 4085,
    "Sandbox": 3810,
    "Roguelike": 1716,
    "Roguelite": 42604,
    "Turn-Based Strategy": 1681,
    "City Builder": 3025,
}


def clean_price(text):
    if not text:
        return None
    text = text.strip()
    if text.lower() == 'free':
        return 0.0
    match = re.search(r'[\d,]+\.\d{2}', text)
    return float(match.group().replace(',', '')) if match else None


def scrape_page(page_num, tag_ids, max_price_cents=None):
    url = f'https://store.steampowered.com/search/?sort_by=Released_DESC&os=win&cc=in&page={page_num}'
    if tag_ids:
        url += f'&tags={",".join(map(str, tag_ids))}'
    if max_price_cents is not None:
        url += f'&maxprice={max_price_cents / 100:.2f}'

    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'lxml')
    games = soup.find_all('a', class_='search_result_row')

    if not games:
        return [], False

    rows = []
    for g in games:
        title_el = g.find('span', class_='title')
        release_el = g.find('div', class_='search_released')
        discount_el = g.find('div', class_='discount_pct')
        orig_price_el = g.find('div', class_='discount_original_price')
        final_price_el = g.find('div', class_='discount_final_price')

        rows.append({
            'Title': title_el.text.strip() if title_el else '',
            'Release Date': release_el.text.strip() if release_el else '',
            'Discount %': discount_el.text.strip() if discount_el else '',
            'Original Price': clean_price(orig_price_el.text if orig_price_el else None),
            'Final Price': clean_price(final_price_el.text if final_price_el else None),
            'URL': g.get('href', '').split('?')[0],
        })
    return rows, True


class SteamScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam Store Scraper")
        self.geometry("900x650")
        self.resizable(True, True)
        self.results = []

        self._build_filters_panel()
        self._build_results_panel()
        self._build_status_bar()

    # UI construction

    def _build_filters_panel(self):
        frame = ttk.LabelFrame(self, text="Filters")
        frame.pack(fill="x", padx=10, pady=10)

        # Tags checklist
        tk.Label(frame, text="Tags (select any):").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        tag_frame = ttk.Frame(frame)
        tag_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        self.tag_vars = {}
        cols = 4
        for i, tag in enumerate(TAG_IDS.keys()):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(tag_frame, text=tag, variable=var)
            cb.grid(row=i // cols, column=i % cols, sticky="w", padx=4, pady=2)
            self.tag_vars[tag] = var

        # Price
        tk.Label(frame, text="Max price (INR):").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.price_entry = ttk.Entry(frame, width=10)
        self.price_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10)
        self.price_entry.insert(0, "")  # blank = no limit

        # Pages
        tk.Label(frame, text="Pages to scrape:").grid(row=1, column=2, sticky="w", padx=5, pady=10)
        self.pages_entry = ttk.Entry(frame, width=6)
        self.pages_entry.grid(row=1, column=3, sticky="w", padx=5, pady=10)
        self.pages_entry.insert(0, "3")

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)

        self.scrape_btn = ttk.Button(btn_frame, text="Scrape", command=self.start_scrape)
        self.scrape_btn.pack(side="left", padx=5)

        self.save_btn = ttk.Button(btn_frame, text="Save to CSV", command=self.save_csv, state="disabled")
        self.save_btn.pack(side="left", padx=5)

    def _build_results_panel(self):
        frame = ttk.LabelFrame(self, text="Results")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("Title", "Release Date", "Discount %", "Original Price", "Final Price")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")
        self.tree.column("Title", width=280)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # double-click to open game page in browser
        self.tree.bind("<Double-1>", self.open_selected_url)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready.")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    # Behavior

    def start_scrape(self):
        selected_tags = [tag for tag, var in self.tag_vars.items() if var.get()]
        tag_ids = [TAG_IDS[t] for t in selected_tags]

        price_raw = self.price_entry.get().strip()
        try:
            max_price = float(price_raw) if price_raw else None
        except ValueError:
            messagebox.showerror("Invalid input", "Max price must be a number.")
            return

        pages_raw = self.pages_entry.get().strip()
        try:
            num_pages = int(pages_raw) if pages_raw else 3
        except ValueError:
            messagebox.showerror("Invalid input", "Pages must be a whole number.")
            return

        self.scrape_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.status_var.set("Scraping... this may take a moment.")

        # Run scraping in background
        thread = threading.Thread(target=self._scrape_worker, args=(tag_ids, max_price, num_pages), daemon=True)
        thread.start()

    def _scrape_worker(self, tag_ids, max_price, num_pages):
        max_price_cents = int(max_price * 100) if max_price is not None else None
        all_rows = []

        for page in range(1, num_pages + 1):
            self._set_status(f"Fetching page {page} of {num_pages}...")
            try:
                rows, has_results = scrape_page(page, tag_ids, max_price_cents)
            except requests.RequestException as e:
                self._set_status(f"Error: {e}")
                break

            if not has_results:
                break
            all_rows.extend(rows)
            time.sleep(1.5)  # be polite to Steam's servers

        if max_price is not None:
            all_rows = [
                r for r in all_rows
                if r['Final Price'] is None or r['Final Price'] <= max_price
            ]

        self.results = all_rows
        self.after(0, self._populate_results)

    def _set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def _populate_results(self):
        for r in self.results:
            price_str = (
                "Free" if r['Final Price'] == 0.0
                else f"₹{r['Final Price']:.2f}" if r['Final Price'] is not None
                else "N/A"
            )
            orig_str = f"₹{r['Original Price']:.2f}" if r['Original Price'] is not None else ""
            self.tree.insert(
                "", "end",
                values=(r['Title'], r['Release Date'], r['Discount %'], orig_str, price_str),
                tags=(r['URL'],)
            )

        self.status_var.set(f"Done. {len(self.results)} games found.")
        self.scrape_btn.config(state="normal")
        self.save_btn.config(state="normal" if self.results else "disabled")

    def open_selected_url(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        url_tags = item.get("tags")
        if url_tags:
            import webbrowser
            webbrowser.open(url_tags[0])

    def save_csv(self):
        if not self.results:
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)
        messagebox.showinfo("Saved", f"Results saved to {filename}")


if __name__ == "__main__":
    app = SteamScraperGUI()
    app.mainloop()