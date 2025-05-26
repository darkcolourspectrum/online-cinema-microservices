-- Создание пользователей и баз данных для микросервисов

-- Auth Service Database
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE DATABASE auth_db OWNER auth_user;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- Movie Service Database  
CREATE USER movie_user WITH PASSWORD 'movie_password';
CREATE DATABASE movie_db OWNER movie_user;
GRANT ALL PRIVILEGES ON DATABASE movie_db TO movie_user;