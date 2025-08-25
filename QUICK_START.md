# 🚀 دليل التشغيل السريع

## ⚡ خطوات سريعة للتشغيل

### 1️⃣ المتطلبات الأساسية
```bash
# تأكد من تثبيت:
# - Python 3.10+
# - PostgreSQL 17+
# - Redis
```

### 2️⃣ إعداد قاعدة البيانات
```bash
# فتح psql
psql -U postgres

# إنشاء قاعدة البيانات
CREATE USER style_recommender WITH PASSWORD 'style_recommender';
ALTER USER style_recommender WITH SUPERUSER;
CREATE DATABASE "style_recommendation_system";
CREATE EXTENSION IF NOT EXISTS vector;
\q
```



### 3️⃣ إعداد البيئات الافتراضية
```bash
# بعد تنزيل وتثبيت بايثون 3.10.0
py -3.10 -m venv style2vec_env
```

### 4️⃣ إعداد بيئة Style2Vec
```bash
# تفعيل بيئة Style2Vec
style2vec_env\Scripts\activate

# تثبيت TensorFlow داخل بيئة style2vec الافتراضية
pip install tensorflow==2.10.0
pip install keras==2.10.0
pip install pillow numpy h5py
pip install gdown==4.7.3
pip install requests==2.32.4
```

# يمكن إختبار إضافة المنتج حيث يتم عمل embedding له بشكل مباشر فور إضافته 
```bash
python test_product.py
```

### 6️⃣ تشغيل النظام
```bash
# Terminal 1: Django Server
python manage.py makemigrations
python manage.py migrate
python manage.py seed_db
python manage.py runserver

# Terminal 2: Celery Worker
celery -A fashionRecommendationSystem worker --loglevel=info --pool=solo
```

### 7️⃣ الوصول للنظام
- **لوحة الإدارة**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/
- **Postman Collection**: `FashionRecommendation.postman_collection.json`

## 🔐 الحسابات الافتراضية
- **Admin**: `admin` / `password123`
- **Test User**: `Test` / `password123`



## ⚠️ ملاحظات مهمة
1. **تأكد من تشغيل Redis** قبل تشغيل Celery
2. **تأكد من وجود النماذج** في مجلد `ai_models/`
3. **استخدم البيئات الافتراضية المناسبة** لكل عملية
4. **راجع README.md** للحصول على تفاصيل أكثر

## 🆘 استكشاف الأخطاء
- **خطأ في قاعدة البيانات**: تحقق من اتصال PostgreSQL
- **خطأ في Redis**: تأكد من تشغيل Redis
- **خطأ في Style2Vec**: تحقق من البيئة الافتراضية والنماذج
- **خطأ في الـ embeddings**: تحقق من أبعاد الـ vectors (2048)

## 📞 المساعدة
- راجع `README.md` للدليل التفصيلي
- راجع قسم "استكشاف الأخطاء" في README
- تحقق من ملفات الـ logs للتفاصيل 