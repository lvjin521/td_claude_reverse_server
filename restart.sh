pids=$(ps -ef | grep 'app_server.claude_server' | grep -v grep | awk '{print$2}')
for pid in $pids
do
kill -9 $pid
echo  "killed $pid"
done


cd /app/product/td_claude_server

gunicorn -c config/gunicorn.py app_server.claude_server:app

echo 'restart'
