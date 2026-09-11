Nama : Nadhif Aydin Adinandra

NPM : 2506537745

Kelas : PBP E

### Tugas 1

1. Ya, saya menggunakan elemen semantik HTML5 seperti `<section>` dan `<article>` dalam struktur website. `<section>` saya gunakan untuk membagi halaman menjadi beberapa bagian seperti Profile, Education, Projects, dan Contact, sedangkan `<article>` digunakan untuk bagian yang memiliki konten tersendiri seperti setiap project dan riwayat pendidikan. Penggunaan elemen tersebut membuat struktur HTML lebih terorganisir dan memudahkan saya dalam mengatur serta memahami bagian-bagian dari static web yang dibuat.

2. Tantangan yang saya temukan saat membuat website responsive adalah menyesuaikan ukuran dan posisi elemen, terutama bagian foto, teks, navigation, dan project cards ketika ukuran layar menjadi lebih kecil. Saya menggunakan CSS media query untuk mengubah layout dari beberapa kolom menjadi satu kolom pada mobile. Saya memprioritaskan informasi utama seperti nama, foto, dan deskripsi agar tetap mudah dilihat, sementara elemen yang tidak terlalu penting dibuat lebih kecil atau disusun ulang.

3. Karena website ini masih berupa static web, informasi yang ditampilkan masih harus ditulis langsung di HTML dan belum dapat dikelola secara dinamis. Selain itu, form contact belum dapat memproses data secara langsung melalui website tanpa bantuan backend. Pada iterasi berikutnya, saya ingin menambahkan fungsionalitas dinamis menggunakan Django, seperti contact form yang dapat mengirim pesan ke email, serta sistem untuk mengelola informasi portfolio tanpa harus mengubah HTML secara manual.

### Tugas 2

1. Ketika pengguna membuka halaman portofolio baru, permintaan pertama kali diterima oleh proyek Django melalui `urls.py` proyek. File `urls.py` proyek bertugas mengarahkan URL tertentu ke `urls.py` aplikasi, yaitu `main/urls.py`. Di `main/urls.py`, rute `portfolio/` dipetakan ke fungsi `show_portfolio` pada `main/views.py`. Fungsi view kemudian mengambil data dari model `PortfolioItem` melalui ORM Django, misalnya `PortfolioItem.objects.order_by("created_at")`. Setelah data siap, view mengirimkan data tersebut ke template `portfolio.html` yang berisi HTML dan logika Django Template Language. Template lalu melakukan perulangan dengan `{% for item in portfolio_items %}` untuk menampilkan tiap objek, dan jika data kosong, template menampilkan pesan kondisi kosong. Terakhir, hasil render dikirim ke browser agar pengguna melihat halaman portofolio.

2. Data bagian portofolio sebaiknya disimpan pada model dan bukan ditulis langsung di template karena model membuat data lebih rapi, terstruktur, dan mudah dikelola. Jika data ditulis langsung di template, setiap perubahan data harus mengubah file HTML secara manual, sehingga lebih rentan terhadap kesalahan dan sulit dikelola saat jumlah data bertambah. Dengan model, kita dapat menambah, mengubah, atau menghapus data melalui database dan aplikasi tetap dapat menampilkan data yang terbaru. Hal ini juga memudahkan pengembangan karena data bisa diproses lebih lanjut, seperti filtering, sorting, dan integrasi ke fitur lain di masa depan.

3. `makemigrations` dan `migrate` memiliki fungsi yang berbeda pada Django. `makemigrations` digunakan untuk membuat file migrasi berdasarkan perubahan yang terjadi pada model, seperti menambahkan field baru, mengubah tipe field, atau membuat model baru. Sementara `migrate` digunakan untuk menerapkan migrasi tersebut ke database agar struktur database sesuai dengan model saat ini. Contoh perubahan model yang membutuhkan kedua perintah adalah ketika kita menambahkan model `PortfolioItem` ke `main/models.py`. Pertama, kita menjalankan `python manage.py makemigrations` untuk menghasilkan file migrasi `0002_portfolioitem.py`, lalu `python manage.py migrate` untuk menerapkan perubahan ke database sehingga tabel `PortfolioItem` dapat dibuat dan digunakan.

### AI Disclosure

Saya menggunakan ChatGPT sebagai bantuan dalam mengembangkan website ini. AI membantu memberikan saran mengenai struktur HTML, styling CSS, responsive layout, penambahan section seperti Projects, Education, dan Contact, serta membantu menjelaskan beberapa konsep yang saya gunakan. Saya tetap menyesuaikan isi, data pribadi, desain, dan struktur website secara manual agar sesuai dengan portfolio yang saya buat. Saya juga melakukan pengecekan dan perubahan terhadap kode yang diberikan agar dapat berjalan sesuai kebutuhan proyek.