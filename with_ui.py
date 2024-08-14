import tkinter as tk
import crawler
import threading
from tkinter import font


root = tk.Tk()
root.title("Crawler UI")

canvas = tk.Canvas(root, width=1000, height=600, bg="white")
canvas.pack()


def run_crawler():
    crawler.start_from(crawler.START)

crawler.REQUEST_SLEEP = .2
t = threading.Thread(target=run_crawler, daemon=True)
t.start()

def draw_tick():
    canvas.delete("all")
    detected_domains = list(set([url.page for url in crawler.to_test_urls]))
    canvas.create_text(10, 10, text=f"C: {crawler.counter} / PPM: {crawler.pinpoint_mode} - Link Pool Size: {len(crawler.to_test_urls)} with {len(detected_domains)} pages", fill="black", anchor="nw")
    
    no_font = font.Font(family='Helvetica', size=8, weight='normal')
    canvas.create_text(10, 40, text=f"--- Requested ({len(crawler.tested_urls)}) ---\n"+"\n".join([str(url) for url in crawler.tested_urls[-10:]]), fill="green", font=no_font, anchor="nw")    
    canvas.create_text(10, 200, text=f"Filtered:\n"+"\n".join([str(url) for url in crawler.filtered_urls]), fill="red", font=no_font, anchor="nw", width=400)    

    if len(crawler.page_sublink_qualities) > 0:
        srtd = {k: v for k, v in sorted(crawler.page_sublink_qualities.items(), key=lambda item: item[1][0]/item[1][1], reverse=True)}
        canvas.create_text(500, 10, text="\n".join([f"{page}: {round(crawler.get_average_sublink_quality(page), 2)} ({data[1]} - {len([url for url in crawler.to_test_urls if url.page == page])})" for page, data in srtd.items()][:30]), fill="black", font=no_font, anchor="nw")


    root.after(500, draw_tick)

draw_tick()
root.mainloop()

