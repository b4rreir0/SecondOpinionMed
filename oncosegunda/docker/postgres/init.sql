-- docker/postgres/init.sql
-- Script de inicialización de la base de datos PostgreSQL

-- Crear usuario para la aplicación
CREATE USER IF NOT EXISTS oncosegunda_user WITH PASSWORD 'changeme123';

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS oncosegunda_prod
    OWNER oncosegunda_user
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE oncosegunda_prod TO oncosegunda_user;

-- Conectar a la base de datos
\c oncosegunda_prod;

-- Crear esquema si es necesario
-- CREATE SCHEMA IF NOT EXISTS oncosegunda AUTHORIZATION oncosegunda_user;

-- Configuraciones adicionales de PostgreSQL
ALTER DATABASE oncosegunda_prod SET timezone = 'UTC';
ALTER DATABASE oncosegunda_prod SET default_transaction_isolation = 'read committed';