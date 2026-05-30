FROM nginx:alpine

# 複製所有靜態檔案到 nginx 預設目錄
COPY . /usr/share/nginx/html/

# 移除不必要的檔案
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/.gitignore

EXPOSE 80
