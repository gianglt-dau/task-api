# 🚀 LAB: Deploy ứng dụng `task-api` bằng GitHub Actions + WSL Runner + GHCR

---

# 🎯 1. Mục tiêu

Sau bài lab này, sinh viên sẽ:

* Hiểu quy trình CI/CD hiện đại
* Biết build Docker image bằng GitHub Actions
* Biết sử dụng **GitHub Container Registry (GHCR)**
* Biết deploy bằng **self-hosted runner trên WSL**
* Hiểu nguyên tắc:

👉 **Server chỉ pull & run — không build**

---

# 🏗️ 2. Kiến trúc hệ thống

```text
Local (code)
   ↓ git push
GitHub Actions (build image)
   ↓
GHCR (ghcr.io)
   ↓
WSL Runner (deploy)
   ↓
Docker container task-api
```

---

# 🧰 3. Chuẩn bị

## 3.1. Local

* Git
* VS Code
* GitHub account

---

## 3.2. WSL

* Ubuntu (WSL2)
* Docker đã cài

Kiểm tra:

```bash
docker ps
```

---

# 📦 4. Tạo ứng dụng `task-api`

## 📍 Thực hiện ở Local

```bash
mkdir task-api
cd task-api
```

---

## 4.1. main.py

```python
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "task-api running",
        "env": os.getenv("APP_ENV", "dev")
    }

@app.get("/tasks")
def tasks():
    return [{"id": 1, "title": "Learn CI/CD"}]
```

---

## 4.2. requirements.txt

```txt
fastapi
uvicorn
```

---

## 4.3. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# 🌐 5. Đưa code lên GitHub

## 📍 Local

```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/<USERNAME>/task-api.git
git push -u origin main
```

---

# ⚙️ 6. Cài self-hosted runner trên WSL

---

## 📍 Bước 1 — Local (trình duyệt)

Vào:

```text
Repo → Settings → Actions → Runners → New self-hosted runner
```

Chọn:

* Linux
* x64

---

## 📍 Bước 2 — WSL

```bash
mkdir -p ~/actions-runner-task-api
cd ~/actions-runner-task-api
```

---

## 📍 Bước 3 — WSL (copy từ GitHub)

```bash
curl -o runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.333.1/actions-runner-linux-x64-2.333.1.tar.gz
tar xzf runner.tar.gz
```

---

## 📍 Bước 4 — cấu hình

```bash
./config.sh --url https://github.com/<USERNAME>/task-api --token <TOKEN>
```

Nhập:

* name: `wsl-runner`
* labels: `wsl,docker,task-api`

---

## 📍 Bước 5 — chạy runner

```bash
./run.sh
```

👉 thấy:

```text
Listening for Jobs
```

---

## 📍 Bước 6 — chạy nền

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

---

# 🧪 7. Chuẩn bị môi trường deploy

## 📍 WSL

```bash
sudo mkdir -p /opt/task-api
sudo nano /opt/task-api/.env
```

```env
APP_ENV=production
```

```bash
sudo chown -R $USER:$USER /opt/task-api
```

---

# 🏗️ 8. Workflow build (GHCR)

## 📍 Local

`.github/workflows/build.yml`

```yaml
name: Build and Push GHCR Image

on:
  push:
    branches: ["main"]

env:
  IMAGE: ghcr.io/${{ github.repository_owner }}/task-api

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ env.IMAGE }}:latest
            ${{ env.IMAGE }}:${{ github.sha }}
```

---

# 🚀 9. Workflow deploy

## 📍 Local

`.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  workflow_run:
    workflows: ["Build and Push GHCR Image"]
    types: [completed]

jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: [self-hosted, Linux, X64, wsl, docker, task-api]

    steps:
      - name: Login GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin

      - name: Pull image
        run: docker pull ghcr.io/${{ github.repository_owner }}/task-api:latest

      - name: Stop old container
        run: |
          docker stop task-api || true
          docker rm task-api || true

      - name: Run container
        run: |
          docker run -d \
            --name task-api \
            -p 8001:8000 \
            --env-file /opt/task-api/.env \
            ghcr.io/${{ github.repository_owner }}/task-api:latest
```

---

# ▶️ 10. Chạy lab

## 📍 Local

```bash
git add .
git commit -m "add ci cd"
git push
```

---

# 🔍 11. Kiểm tra

## 📍 Local

```bash
curl http://localhost:8001
```

---

## 📍 WSL

```bash
docker ps
docker logs task-api
```

---

# 🧪 12. Bài tập

---

## Bài 1

Sửa message → push → auto deploy

---

## Bài 2

Thêm endpoint `/hello`

---

## Bài 3

Đổi port sang `9001`

---

## Bài 4 (nâng cao)

Deploy theo SHA

---

# ❌ 13. Lỗi thường gặp

| Lỗi                  | Nguyên nhân        |
| -------------------- | ------------------ |
| Runner không chạy    | chưa start service |
| Không deploy         | sai tên workflow   |
| Không pull image     | chưa login GHCR    |
| Container không chạy | thiếu `.env`       |
| Job không nhận       | sai label          |

---

# 🧠 14. Tổng kết

| Thành phần     | Vai trò   |
| -------------- | --------- |
| Local          | viết code |
| GitHub Actions | build     |
| GHCR           | lưu image |
| WSL runner     | deploy    |
| Docker         | chạy app  |

---

