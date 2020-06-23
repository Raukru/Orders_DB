from flask import Flask, render_template, request, flash
import mysql.connector

app = Flask(__name__)

# Логин и пароль для подключения к БД
__user = "root"
__password = "bobZx8000"
__database_name = 'mybd'
__host = '127.0.0.1'

__SQL_r1 = """SELECT  `id_menu`, `Name`, SUM(Sum), `Menu`.`Price`*SUM(Sum)
FROM `Order` JOIN  `Order_line` USING (id_order) JOIN `Menu` USING (id_menu)
WHERE (MONTH(Date_accept)=03) AND (YEAR(Date_accept)=2017)
GROUP BY `id_menu`;"""

__SQL_r2 = """SELECT `id_waiter` , `Surname`,
COUNT(id_order), SUM(`Order`.`Price`) 
FROM `Waiter` JOIN `Order` USING (id_waiter)
WHERE (MONTH(`Order`.`Date_accept`)=03) AND (YEAR(`Order`.`Date_accept`)=2017)
GROUP BY `id_waiter`  ;"""

__SQL_r3 = """SELECT * FROM `Waiter`
WHERE `Date_accept` = ( SELECT MAX(Date_accept) FROM `Waiter` );"""

__SQL_r4 = """SELECT *
FROM `Waiter` LEFT JOIN `Order` USING (id_waiter)
WHERE `Order`.`id_waiter` is NULL;"""

__SQL_r5 = """SELECT *
From `Waiter` LEFT JOIN (SELECT * FROM `Order`
WHERE (MONTH(Date_accept)=03) AND (YEAR(Date_accept)=2013)) `Order2013` USING (id_waiter)
WHERE `Order2013`.`id_waiter` is NULL;"""

__SQL_r6 = """CREATE VIEW `Order2017` as
SELECT `id_menu` , `Name`, `Code`, `Weight`, `Menu`.`Price` AS `Menu.Price` 
FROM `Order_line` JOIN `Menu` USING (id_menu) JOIN `Order` USING (id_order)
WHERE (MONTH(Date_accept)=04) AND (YEAR(Date_accept)=2017);"""

__SQL_proc = """
CREATE DEFINER=`root`@`localhost` PROCEDURE `Blydo`(o_year integer,o_month integer)
BEGIN
DECLARE id_otc,kolvo_z,AAA integer;
DECLARE nazv varchar(25);
DECLARE done integer DEFAULT 0;
DECLARE REP CURSOR FOR
SELECT id_menu,Name,SUM(Sum)
FROM `menu` JOIN `Order_line` USING (id_menu) JOIN `Order` USING (id_order)
WHERE (YEAR(Date_accept)=o_year) AND (MONTH(Date_accept)=o_month)
GROUP BY id_menu;
DECLARE CONTINUE HANDLER
FOR sqlstate '02000' SET done=1;
SELECT COUNT(*) INTO AAA
FROM `otch1`
WHERE (s_year=o_year) AND (s_month=o_month);
IF AAA<1 THEN BEGIN
OPEN REP;
REPEAT
FETCH REP INTO id_otc,nazv,kolvo_z;
IF done=0 THEN
INSERT INTO `otch1` VALUES(NULL,id_otc,o_year,o_month,nazv,kolvo_z);
END IF;
UNTIL done=1
END REPEAT;
CLOSE REP;
SELECT "Otchet uspeshno sozdan";
END;
ELSE SELECT "Otchet uzhe sushestvuet";
END IF;
END;

"""


def bd_connect(usr=__user, passw=__password):
    try:
        conn = mysql.connector.connect(user=usr, password=passw, host=__host, database=__database_name)
    except:
        conn = None
    return conn


def sql_request(sql:str):
    conn = bd_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
    except:
        print("SQL request error")
        result = None
    conn.close()
    cursor.close()
    conn.disconnect()
    return result


# Проверка соединения с БД
@app.route('/test')
def test_bd_connection():
    if bd_connect() == None:
        return "BD connection failed"
    else:
        return "BD connection success"


@app.route('/')
def index():
    return render_template("menu.html")


@app.route('/request_1')
def request_1():
    result = sql_request(__SQL_r1)
    return render_template("request_1.html", result=result)


@app.route('/request_2')
def request_2():
    result = sql_request(__SQL_r2)
    return render_template("request_2.html", result=result)


@app.route('/request_3')
def request_3():
    result = sql_request(__SQL_r3)
    return render_template("request_3.html", result=result)


@app.route('/request_4')
def request_4():
    result = sql_request(__SQL_r4)
    return render_template("request_4.html", result=result)


@app.route('/request_5')
def request_5():
    result = sql_request(__SQL_r5)
    return render_template("request_5.html", result=result)


@app.route('/request_6')
def request_6():
    conn = bd_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(__SQL_r6)
    except:
        cursor.execute("drop view Order2017")
        cursor.execute(__SQL_r6)
    conn.disconnect()
    result = sql_request("select * from Order2017;")
    return render_template("request_6.html", result=result)


@app.route('/create_report', methods=['GET', 'POST'])
def create_report():
    if request.method == 'POST':
        year = request.form['year']
        month = request.form['month']
        conn = bd_connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""CREATE TABLE otch1 (nul VARCHAR(20), id INT NOT NULL,
s_year INT NOT NULL, s_month INT NOT NULL, 
name VARCHAR(45) NOT NULL, count INT NOT NULL);""")
        except:
            pass
        try:
            cursor.execute(__SQL_proc)
        except:
            pass
        try:
            for res in cursor.execute("call Blydo({}, {});".format(year, month), multi=True):
                for row in res:
                    print(row[0])
        except:
            return "Can't call procedure with arguments '{}' and '{}'".format(year, month)
        conn.commit()
        conn.close()
        cursor.close()
        conn.disconnect()
    return render_template("create_report.html")


@app.route('/choice_report')
def choice_report():
    # if request.method == 'POST':
    #     year = request.form['year']
    #     month = request.form['month']
    #     print("Posted - {}-{}".format(year, month))
    # else:
    #     print("Get")
    return render_template("choice_report.html")


@app.route('/view_report', methods=['GET', 'POST'])
def view_report():
    if request.method == 'POST':
        year = request.form['year']
        month = request.form['month']
        try:
            result = sql_request("""select * from otch1 where `s_year`={} AND `s_month`={};""".format(year, month))
        except:
            result = "None"
            return "Report doesn't exist"
    return render_template("view_report.html", result=result, year=year, month=month)

if __name__ == "__main__":
    app.run(debug=True)