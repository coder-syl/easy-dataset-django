SELECT 
    app.id,
    app.name,
    app.desc,
    app.icon,
    app.type,
    app.create_time,
    u.username,
    app.dialogue_number,
    app.dataset_setting,
    app.model_setting,
    app.work_flow
FROM application app
LEFT JOIN users_user u ON app.user_id = u.id
WHERE app.id IN (
    SELECT DISTINCT application_id 
    FROM application_work_flow_version 
    WHERE publish_user_id IS NOT NULL
)
ORDER BY app.create_time DESC
