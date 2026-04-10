docker_canvas:
	docker exec -it canvas_ai_db psql -U myuser -d canvas_ai -c "$(q)";