# TikHub 接口约定

默认服务地址：`https://api.tikhub.io`。

|用途|方法|路径|参数|
|---|---|---|---|
|账号搜索|POST|`/api/v1/douyin/search/fetch_user_search_v2`|`keyword`, `cursor`|
|账号资料|GET|`/api/v1/douyin/app/v3/handler_user_profile`|`sec_user_id`|
|作品列表|GET|`/api/v1/douyin/app/v3/fetch_user_post_videos`|`sec_user_id`, `max_cursor`, `count`, `sort_type`|
|作品评论|GET|`/api/v1/douyin/app/v3/fetch_video_comments`|`aweme_id`, `cursor`|

请求头使用 `Authorization: Bearer $TIKHUB_API_KEY`。响应原文应保存到任务目录，便于审计和失败重试。TikHub 返回的 `user_id` 在账号搜索结果中作为 `sec_user_id` 使用；搜索结果必须与输入的 `unique_id` 或抖音号精确匹配，无法精确匹配时标记失败。
