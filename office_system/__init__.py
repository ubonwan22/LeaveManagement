#ตัวแปลงให้ PyMySQL  ใช้แทน mysqlclient
import pymysql
pymysql.install_as_MySQLdb() #โดยปกติ Django เวลาที่จะคุย MySQL จะผ่านโมดูล MySQLdb แต่พอมีบรรทัดนี้ ทำให้ pymsql กลายเป็น MySQLdb โดยไฟล์นี้จะรันทันทีที่รัน Project