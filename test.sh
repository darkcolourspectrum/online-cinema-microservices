#!/bin/bash

# Массовый тест
BASE_URL="http://localhost"

echo "=== Создаем тестовых пользователей ==="

# Пользователь 1
curl -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@test.com", "username": "user1", "password": "password123"}' \
  -s | jq .

# Пользователь 2  
curl -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user2@test.com", "username": "user2", "password": "password123"}' \
  -s | jq .

echo "=== Получаем токены ==="

# Токен пользователя 1
TOKEN1=$(curl -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@test.com", "password": "password123"}' \
  -s | jq -r .access_token)

# Токен пользователя 2
TOKEN2=$(curl -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user2@test.com", "password": "password123"}' \
  -s | jq -r .access_token)

echo "Токены получены: $TOKEN1 и $TOKEN2"

echo "=== Создаем комментарии от разных пользователей ==="

# Комментарии от пользователя 1
curl -X POST $BASE_URL/api/comments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"movie_id": 1, "content": "Фантастический фильм! 10 из 10!", "rating": 10}' \
  -s | jq .

curl -X POST $BASE_URL/api/comments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"movie_id": 1, "content": "Отличная операторская работа"}' \
  -s | jq .

# Комментарии от пользователя 2
curl -X POST $BASE_URL/api/comments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"movie_id": 1, "content": "Неплохо, но есть недостатки", "rating": 6}' \
  -s | jq .

curl -X POST $BASE_URL/api/comments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"movie_id": 1, "content": "Согласен с предыдущим комментатором", "parent_id": 1}' \
  -s | jq .

echo "=== Тестируем лайки ==="

# Пользователь 1 лайкает комментарий пользователя 2
curl -X POST $BASE_URL/api/comments/3/like \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"is_like": true}' \
  -s | jq .

# Пользователь 2 дизлайкает комментарий пользователя 1
curl -X POST $BASE_URL/api/comments/1/like \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"is_like": false}' \
  -s | jq .

echo "=== Получаем статистику ==="

curl $BASE_URL/api/comments/movie/1/stats -s | jq .

echo "=== Получаем все комментарии ==="

curl $BASE_URL/api/comments/movie/1 -s | jq .

echo "=== Тест завершен! ==="