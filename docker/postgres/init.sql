-- 告诉PostgreSQL把vector扩展打开  Docker镜像虽然已经安装了pgvector，但数据库里面还需要

CREATE EXTENSION IF NOT EXISTS vector;