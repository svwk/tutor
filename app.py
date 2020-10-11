import os
import json
import random


from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
import wtforms
from wtforms import validators


time_values = ["8:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
day_values = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class BookingForm(FlaskForm):
    clientName = wtforms.StringField("Вас зовут", [validators.InputRequired(message="Необходимо ввести имя")])
    clientPhone = wtforms.StringField("Ваш телефон", [validators.InputRequired(message="Необходимо ввести телефон"),
                                                      validators.regexp(
                                                          '^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$',
                                                          message="Телефон должен содержать от 6 до 11 цифр")])
    clientTeacher = wtforms.HiddenField()
    clientWeekday = wtforms.HiddenField("", [validators.any_of(day_values)])
    clientTime = wtforms.HiddenField("", [validators.any_of(time_values)])


class RequestForm(FlaskForm):
    clientName = wtforms.StringField("Вас зовут", [validators.InputRequired(message="Необходимо ввести имя")])
    clientPhone = wtforms.StringField("Ваш телефон", [validators.InputRequired(message="Необходимо ввести телефон"),
                                                      validators.regexp(
                                                          '^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$',
                                                          message="Телефон должен содержать от 6 до 11 цифр")])
    clientGoal = wtforms.RadioField('Какая цель занятий?', default=1,
                                    choices=[("travel", "Для путешествий"), ("study", "Для учебы"),
                                             ("work", "Для работы"), ("relocate", "Для переезда"),
                                             ("coding", "для программирования")])
    clientTime = wtforms.RadioField('Сколько времени есть?', default=1,
                                    choices=[("1-2", "1-2 часа в неделю"), ("3-5", "3-5 часов в неделю"),
                                             ("5-7", "5-7 часов в неделю"), ("7-10", "7-10 часов в неделю")])


weekdays = [("mon", "Понедельник"), ("tue", "Вторник"), ("wed", "Среда"), ("thu", "Четверг"), ("fri", "Пятница"),
            ("sat", "Суббота"), ("sun", "Воскресенье")]

#загрузка данных
try:
    f = open('data.json', 'r')
    goals, teachers = (json.load(f)).values()
    f.close()
except FileNotFoundError:
    from data import goals,teachers
    with open("data.json", "w") as f:
        json.dump({'goals': goals, 'teachers': teachers}, f, indent=4, ensure_ascii=False)

#with open("data.json", "r") as r:
#    goals, teachers = (json.load(r)).values()

app = Flask(__name__)
csrf = CSRFProtect(app)
#SECRET_KEY = os.urandom(43)  # Создаем рандомнй ключ
SECRET_KEY="ezfremfejt4ijg45jgdl;g"
app.config['SECRET_KEY'] = SECRET_KEY


def add_to_json(data_to_write, file):
    records = []
    try:
        with open(file, 'r') as jfr:
            records = json.load(jfr)
    except:
        pass
    finally:
        with open(file, 'w') as jf:
            records.append(data_to_write)
            json.dump(records, jf, indent=4, ensure_ascii=False)


@app.route('/')
def render_main():
    selected_list = teachers
    if len(teachers) > 6:
        random.seed()
        selected_list = random.sample(teachers, 6)
    
    return render_template('index.html', goals=goals, teachers=selected_list)


@app.route('/goals/<goal>/')
def render_goals_item(goal):
    selected_list = list(filter(lambda x: goal in x["goals"], teachers))
    return render_template('goal.html', goals=goals, teachers=selected_list, goal=goal)


@app.route('/profiles/<int:id>/')
def render_profiles_item(id):
    t = list(filter(lambda x: x["id"] == id, teachers))
    if t:
        return render_template('profile.html', t=t[0], goals=goals, weekdays=weekdays)
    else:
        return render_template('error.html', text="К сожалению, данной страницы не существует"), 404


@app.route('/request/', methods=['GET', 'POST'])
def render_request():
    form = RequestForm()
    form.clientGoal.data = "travel"
    form.clientTime.data = "5-7"
    return render_template('request.html', form=form)


@app.route('/request_done/', methods=['POST'])
def render_request_done():
    form = RequestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            clientName = form.clientName.data
            clientPhone = form.clientPhone.data
            clientGoal = form.clientGoal.data
            clientTime = form.clientTime.data
            goal = [c[1] for c in form.clientGoal.choices if c[0] == clientGoal]
            time = [c[1] for c in form.clientTime.choices if c[0] == clientTime]
            if goal and time:
                # сохраняем данные
                str = {'clientName': clientName, 'clientPhone': clientPhone, 'clientGoal': goal[0],
                       'clientTime': time[0]}
                add_to_json(str, 'request.json')
                
                # переходим на request_done
                return render_template('request_done.html', clientName=clientName, clientPhone=clientPhone,
                                       clientGoal=goal[0], clientTime=time[0])
            else:
                return render_template('error.html', text="К сожалению, вы ввели неверные данные"), 404
        else:
            #отправляем форму назад
            return render_template('request.html', form=form)
        
    return render_template('error.html', text="К сожалению, данной страницы не существует"), 404


@app.route('/booking/<int:id>/<weekday>/<time>/', methods=['GET', 'POST'])
def render_booking_item(id, weekday, time):
    form = BookingForm()
    # Если данные были отправлены
    if request.method == "POST":
        if form.validate_on_submit():
            # получаем данные
            clientName = form.clientName.data
            clientPhone = form.clientPhone.data
            clientTeacher = int(form.clientTeacher.data)
            clientWeekday = form.clientWeekday.data
            clientTime = form.clientTime.data
            
            days = [c[1] for c in weekdays if c[0] == clientWeekday]
            if not days:
                return render_template('error.html', text="К сожалению, вы ввели неверный день недели"), 404
            
            for i in range(0, len(teachers)):
                if teachers[i]["id"] == clientTeacher:
                    c = teachers[i]["free"][clientWeekday][clientTime]
                    if c:
                        teachers[i]["free"][clientWeekday][clientTime] = False
                        
                        # сохраняем данные
                        with open("data.json", "w") as f:
                            json.dump({'goals': goals, 'teachers': teachers}, f, ensure_ascii=False)
                        str = {'clientName': clientName, 'clientPhone': clientPhone, 'clientTeacher': clientTeacher,
                               'clientWeekday': clientWeekday, 'clientTime': clientTime}
                        add_to_json(str, 'booking.json')
                        
                        # переходим на booking_done
                        return render_template('booking_done.html', clientName=clientName, clientPhone=clientPhone,
                                               clientWeekday=days[0], clientTime=clientTime)
                    else:
                        return render_template('error.html', text="К сожалению, указанное время занято"), 200
            
            return render_template('error.html', text="К сожалению, указанного преподавателя не существует"), 404
        else:
            # если данные post и get отличаются, приводим их к одному виду
            time = form.clientTime.data
            id = int(form.clientTeacher.data)
            weekday = form.clientWeekday.data
    
    # Если данные еще НЕ были отправлены или неверны
    # выводим форму
    t = list(filter(lambda x: x["id"] == id, teachers))
    if t and (time in time_values) and (weekday in day_values):
        days = [c for c in weekdays if c[0] == weekday]
        if len(days) > 0:
            form.clientTime.data = time
            form.clientTeacher.data = id
            form.clientWeekday.data = weekday
            return render_template('booking.html', form=form, t=t[0], weekday=days[0], time=time)
    
    return render_template('error.html', text="К сожалению, вы ввели неверные данные"), 404


@app.errorhandler(404)
def render_not_found(error):
    return render_template('error.html', text="Ничего не нашлось!"), 404


@app.errorhandler(500)
def render_server_error(error):
    return render_template('error.html',
                           text="Что-то не так, но мы все починим:\n{}".format(error.original_exception)), 500


if __name__ == '__main__':
    app.run()
