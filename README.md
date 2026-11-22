# مكتبة إتقان — دليل الموارد والبيانات القرآنية المفتوحة
### Itqan Library — Open-Source Quranic Technology & Datasets Directory

[![Live Website](https://img.shields.io/badge/Website-Live%20on%20GitHub%20Pages-0d6d5b?style=for-the-badge)](https://nandxorandor.github.io/itqan-library)
[![Auto Sync](https://img.shields.io/badge/Auto--Sync-GitHub%20Actions-blue?style=for-the-badge)](https://github.com/nandxorandor/itqan-library/actions)

دليل مجتمعي موثّق ومنظّم يجمع روابط التنزيل المباشرة لحزم التسجيلات الصوتية، نماذج التسميع والذكاء الاصطناعي، خطوط الرسم العثماني، وأدوات المزامنة البرمجية التي أنتجها وشاركها أعضاء [مجتمع إتقان للتقنيات القرآنية](https://community.itqan.dev).

---

## 🌟 مميزات المنصة (Features)
- **روابط تنزيل ومصادر مباشرة:** تحميل فوري لحزم البيانات من Archive.org و HuggingFace و GitHub دون تشتت.
- **ربط بالنقاش الأصلي:** كل مورد يرتبط مباشرة بموضوعه في مجتمع إتقان لمتابعة النقاش مع الكاتب والمطورين.
- **أتمتة الفحص والتحديث الذاتي:** يعمل سكربت مجاني عبر GitHub Actions لفحص نقاشات المجتمع وإضافة أي موارد أو نماذج جديدة تلقائياً.
- **تصفية بالمجلدات:** استعراض سهل حسب التصنيف (صوتيات، نماذج ذكاء اصطناعي، خطوط، أدوات).

---

## 📁 تصنيفات الموارد (Resource Categories)
1. **حزم الصوتيات والتسجيلات (Audio Datasets):** تسجيلات المتعلمين الحقيقية، تسجيلات ترتيل، مشروعات التوقيت ومحاذاة التلاوة.
2. **نماذج الذكاء الاصطناعي والتسميع (AI & ASR Models):** نماذج التجويد (مثل TajweedFormer)، نماذج تفريغ الصوت القرآني، والأوزان المفتوحة.
3. **الخطوط والرسم العثماني (Typography & Fonts):** خطوط مجمع الملك فهد، مصحف عماد، ومختبرات فحص الخطوط.
4. **أدوات المزامنة والتقطيع البرمجي (Tools & Aligners):** أدوات تقطيع الصوتيات الآلية، توليد صور الآيات، ومعالجة النصوص.
5. **واجهات البرمجة والخوادم (APIs & MCP):** خادم MCP الرسمي لمجتمع إتقان ومكتبات الربط.

---

## 🚀 التشغيل المحلي (Run Locally)
يمكنك فتح ملف `index.html` في أي متصفح مباشرة، أو تشغيل خادم محلي:
```bash
python -m http.server 8000
```
ثم افتح: `http://localhost:8000`

---

## 🔄 كيفية عمل التحديث التلقائي (Auto-Sync)
يعمل السكربت `sync_resources.py` تلقائياً عبر GitHub Actions أسبوعياً أو عند التشغيل اليدوي:
```bash
python sync_resources.py
```
يقوم بفحص المواضيع الحديثة في مجتمع إتقان واستخراج روابط المستودعات وحزم البيانات وتحديث `resources.json`.

---

## 🤝 المساهمة (Contributing)
نرحب بمساهمة جميع الإخوة المطورين في إثراء هذه المكتبة، سواء باقتراح روابط جديدة عبر فتح [Issue](https://github.com/nandxorandor/itqan-library/issues) أو تقديم [Pull Request](https://github.com/nandxorandor/itqan-library/pulls).
