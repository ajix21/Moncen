# SEMAR WATCH QA Suite

Test suite lengkap untuk validasi semar-watch v2 (split-service CCTV system).
Mencakup structure checks, API contracts, WebSocket flow, service interaction,
security audit, dan resource monitoring.

---

## Prasyarat

- Python 3.11+
- semar-watch v2 sudah di-generate di direktori induk
- (Opsional) `./start-all.sh` dijalankan untuk test runtime

---

## Setup

```bash
cd semar-watch
chmod +x qa/setup_qa.sh qa/run_qa.sh
./qa/setup_qa.sh
```

---

## Menjalankan Test

### Structure-only (tidak butuh server):
```bash
./qa/run_qa.sh --structure-only
```

### Security-only:
```bash
./qa/run_qa.sh --security-only
```

### Full suite (semua service harus aktif):
```bash
./start-all.sh        # terminal 1
./qa/run_qa.sh        # terminal 2
```

### Satu file spesifik:
```bash
cd qa
source venv/bin/activate
python -m pytest test_02_dashboard_api.py -v --timeout=30
```

---

## File Test

| File | Deskripsi | Butuh Server |
|------|-----------|:---:|
| `test_01_structure.py` | Struktur file, forbidden imports, dependency hygiene | Tidak |
| `test_02_dashboard_api.py` | REST API dashboard (CRUD, events, stats, cv proxy) | Dashboard |
| `test_03_cv_engine_api.py` | REST API CV engine (streams, settings, snapshot) | CV Engine |
| `test_04_websocket.py` | WebSocket flow (dashboard summary, CV broadcast) | Kedua |
| `test_05_service_interaction.py` | Interaksi antar service (shared DB, status sync) | Kedua |
| `test_06_security.py` | CORS, SQL injection, path traversal, info leakage | Dashboard/CV |
| `test_07_resource.py` | Memory usage, CPU idle, stream concurrency limit | Kedua |

---

## Test Naming Convention

- `D` = Dashboard API (test_02)
- `C` = CV Engine API (test_03)
- `W` = WebSocket (test_04)
- `I` = Service Interaction (test_05)
- `SEC` = Security (test_06)
- `R` = Resource (test_07)

---

## Known Skip Conditions

Tests skip automatically (not fail) when:
- Server tidak berjalan (`pytest.skip`)
- psutil tidak tersedia (resource tests)
- Tidak ada CCTV stream terdaftar (CV stream tests)
- Tidak ada pesan WS dalam timeout window

---

## Expected Results (setelah `./start-all.sh`)

```
test_01_structure.py  ..............................  PASS (structural)
test_02_dashboard_api.py  .............  PASS (all API contracts)
test_03_cv_engine_api.py  ..........  PASS (most pass; C04/C06 may flag if CV busy)
test_04_websocket.py  .....  PASS (W04 needs CV engine + active HLS stream)
test_05_service_interaction.py  ........  PASS
test_06_security.py  ............  PASS (SEC03 prints recommendations)
test_07_resource.py  .......  PASS (RAM < 400MB dashboard, < 2GB CV)
```

---

## Catatan Konfigurasi

### pytest-asyncio mode
File `conftest.py` menggunakan `pytest_collection_modifyitems` untuk auto-apply
`@pytest.mark.asyncio` ke semua async test. Jika terjadi error asyncio,
tambahkan ke `pytest.ini` atau `pyproject.toml`:

```ini
[pytest]
asyncio_mode = auto
```

### Timeout
Default timeout 60s per test. Untuk WS tests yang menunggu CV inference,
timeout 60s diperlukan karena `cv_frame_interval` bisa 5–10s.

---

## Integrasi CI

```yaml
# .github/workflows/qa.yml (contoh)
- name: Structure QA (no server)
  run: |
    cd semar-watch
    ./qa/setup_qa.sh
    ./qa/run_qa.sh --structure-only
```
