# TranTest

## خروجی صفحه‌به‌صفحه و قابل fetch

پوشهٔ [`fetchable-pages/`](fetchable-pages/) نسخهٔ ۷۰ صفحه‌ای PDF را به URLهای مستقل تقسیم می‌کند:

- `index.html`: فهرست و لینک همهٔ صفحه‌ها
- `pages/page-001.html` تا `pages/page-070.html`: HTML مستقل هر صفحه همراه متن واقعی در پاسخ HTML
- `images/`: رندر lossless هر صفحه برای حفظ دقیق عکس‌ها، جدول‌ها، فرمول‌ها و شماره‌صفحهٔ چاپی
- `text/`: متن سادهٔ UTF-8 هر صفحه
- `data/`: JSON هر صفحه شامل متن و metadata
- `manifest.json`: فهرست machine-readable همهٔ endpointها و SHA-256 فایل منبع

برای پیش‌نمایش محلی:

```bash
python3 -m http.server 8000 --directory fetchable-pages
```

سپس `http://localhost:8000/` را باز کنید. برای ساخت مجدد خروجی (نیازمند PyMuPDF و Pillow):

```bash
python tools/build_page_folder.py 01.pdf fetchable-pages
```
