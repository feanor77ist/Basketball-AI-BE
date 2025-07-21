1. Giriş ve Genel Tanım
   Bu sistem, basketbol oyuncularına özel highlight videoları oluşturmayı hedeflemektedir.
   Kullanıcı bir maç videosu yükler, sistem bu videoyu analiz ederek oyuncuların önemli anlarını tespit eder,
   sınıflandırır ve profesyonel bir highlight videosu oluşturur.
   Bu doküman, mmaction2 ile güncellenmiş MVP mimarisini içermektedir.

2. Detaylı API Endpoint Yapısı
   [VIDEO]
   POST /api/upload/ → Video yükleme
   POST /api/process/ → Video işleme başlatma
   GET /api/status/<video_id>/ → İşlem durumu

[ACTIONS]
POST /api/actions/infer/ → mmaction2 ile aksiyon tanıma başlatma
GET /api/actions/?video=... → Videoya ait aksiyon listesi (filtrelenebilir)
GET /api/actions// → Belirli aksiyon detayı

[HIGHLIGHTS]
GET /api/highlights/ → Tüm highlight listesi
GET /api/highlights/?player=...&type=3pt → Filtreleme
GET /api/highlights//download/ → MP4 indirme linki

[STATS]
GET /api/stats/<video_id>/ → Video bazlı oyuncu istatistiği
GET /api/stats/<video_id>/download/?format=csv → CSV/JSON

[AUTH]
POST /api/auth/login/ → Kullanıcı girişi
POST /api/auth/register/ → Kayıt

3. Detaylı Veritabanı Yapısı
   [User]

id (UUID), email, password, date_joined
[Video]

id (UUID), user_id, file, upload_date, status, duration
[Player]

id, video_id, jersey_number, team_color, player_id_model
[Action]

id, video_id, player_id, type, start_time, end_time
is_successful, x, y, model_type, confidence, segment_path
[Highlight]

id, video_id, player_id, file, duration, actions (M2M)
[Stats]

id, video_id, player_id, fga_2pt, fgm_2pt, fga_3pt, fgm_3pt, assists, rebounds, points
[Genişleme]

PlayerProfile: user, bio, height, position, club
ScoutProfile: user, organization, filters

4. Detaylı Frontend Dosya Yapısı
   src/
   ├── assets/ → Görseller, logolar
   ├── components/
   │ ├── ui/ → shadcn-ui bileşenleri
   │ ├── forms/ → Form bileşenleri (upload, filtre)
   │ └── common/ → Button, Modal, Spinner vb.
   ├── features/
   │ ├── upload/ → UploadForm, useUpload hook
   │ ├── highlights/ → HighlightList, HighlightCard
   │ ├── stats/ → StatsTable, useStats
   │ └── actions/ → ActionInferButton, useActionInfer
   ├── hooks/ → usePolling, useVideoStatus vb.
   ├── lib/
   │ ├── api.ts → Axios config
   │ ├── endpoints.ts → API route sabitleri
   │ └── utils.ts → Yardımcı fonksiyonlar (cn, formatTime...)
   ├── pages/
   │ ├── Home.tsx
   │ ├── Highlights.tsx
   │ ├── Stats.tsx
   │ └── Login.tsx
   ├── routing/ → AppRoutes.tsx
   ├── types/ → TypeScript tip tanımları
   └── index.css, main.tsx → Tailwind ve giriş dosyaları

5. Celery Görev Yapısı
   @shared_task
   def detect_actions_with_mmaction(video_id):

Video segmentlere ayrılır (örn. her 3 saniye)
mmaction2 modeli init edilir (TSN, SlowFast vb.)
Her segment için inference yapılır
Tahmin sonuçları Action modeline yazılır (type, confidence)
Video.status = 'actions_done' olarak güncellenir

6. mmaction2 ile Aksiyon Tanıma Entegrasyonu
   mmaction2 reposu kullanılarak özelleştirilmiş video segment tahmini yapılır.
   init_recognizer + inference_recognizer fonksiyonları Celery task içinde kullanılır.
   Basketbola özel dataset ile fine-tuning yapılabilir.
   inference sonucu: [(label, confidence)] şeklindedir.
   Her segment için ayrı Action kaydı oluşturulur.

7. Güncel Video İşleme ve Highlight Oluşturma Akışı
   Kullanıcı video yükler (/upload)
   Video işleme başlatılır (/process)
   Celery sırayla çalışır:
   Oyuncu tespiti (YOLOv8 + DeepSORT)
   Top lokalizasyonu & skor analizi
   mmaction2 ile aksiyon tanıma
   Klip kesme (MoviePy/FFmpeg)
   Stats çıkarımı (pandas)
   Video status = 'done'
   Kullanıcı highlight ve istatistik verilerini frontend'den görür

8. Frontend: Action Inference Hook ve UI
   useActionInfer: React Query + Axios ile /api/actions/infer/ endpoint'ini tetikler.
   ActionInferButton: Kullanıcının bu işlemi başlatması için basit bir buton.
   Kullanıcı video bazında inference başlatır, polling ile sonuçları bekleyebilir.
