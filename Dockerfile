FROM archlinux:base-20221030.0.98412

# If you are not in China, please delete the next line to diable the pacman mirror
RUN echo 'Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
RUN pacman -Syu --noconfirm && pacman -S --noconfirm nginx python vim python-pip && useradd -m app
COPY app /app
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY start.sh /start.sh
RUN cd /app && pip install -r requirements.txt
RUN groupadd docker && usermod -aG docker app && chmod +x /start.sh && chown app:app /app
CMD /start.sh