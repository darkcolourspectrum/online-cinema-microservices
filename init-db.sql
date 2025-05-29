
-- Auth Service Database
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE DATABASE auth_db OWNER auth_user;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- Movie Service Database  
CREATE USER movie_user WITH PASSWORD 'movie_password';
CREATE DATABASE movie_db OWNER movie_user;
GRANT ALL PRIVILEGES ON DATABASE movie_db TO movie_user;

-- User Profile Service Database
CREATE USER profile_user WITH PASSWORD 'profile_password';
CREATE DATABASE profile_db OWNER profile_user;
GRANT ALL PRIVILEGES ON DATABASE profile_db TO profile_user;

-- Comments Service Database
CREATE USER comments_user WITH PASSWORD 'comments_password';
CREATE DATABASE comments_db OWNER comments_user;
GRANT ALL PRIVILEGES ON DATABASE comments_db TO comments_user;