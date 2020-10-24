import json
import random
import secrets

from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
import wtforms
from wtforms import validators

TIME_VALUES = ("8:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00")
DAY_VALUES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
TEL_REG = r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$'
WEEKDAYS = (("mon", "Понедельник"), ("tue", "Вторник"), ("wed", "Среда"), ("thu", "Четверг"), ("fri", "Пятница"),
            ("sat", "Суббота"), ("sun", "Воскресенье"))
ALL_DATA = 'data.json'
BOOKING_DATA = 'booking.json'
REQUEST_DATA = 'request.json'


class BookingForm(FlaskForm):
    clientName = wtforms.StringField("Вас зовут", [validators.InputRequired(message="Необходимо ввести имя")])
    clientPhone = wtforms.StringField("Ваш телефон", [validators.InputRequired(message="Необходимо ввести телефон"),
                                                      validators.regexp(
                                                          TEL_REG,
                                                          message="Телефон должен содержать от 6 до 11 цифр")])
    clientTeacher = wtforms.HiddenField()
    clientWeekday = wtforms.HiddenField("",
                                        [validators.any_of(DAY_VALUES, "К сожалению, вы ввели неверный день недели")])
    clientTime = wtforms.HiddenField("", [validators.any_of(TIME_VALUES, "К сожалению, вы ввели неверное время")])


class RequestForm(FlaskForm):
    clientName = wtforms.StringField("Вас зовут", [validators.InputRequired(message="Необходимо ввести имя")])
    clientPhone = wtforms.StringField("Ваш телефон",
                                      [validators.InputRequired(message="Необходимо ввести телефон"),
                                       validators.regexp(
                                           TEL_REG,
                                           message="Телефон должен содержать от 6 до 11 цифр")])
    clientGoal = wtforms.RadioField('Какая цель занятий?', default="travel",
                                    choices=[("travel", "Для путешествий"), ("study", "Для учебы"),
                                             ("work", "Для работы"), ("relocate", "Для переезда"),
                                             ("coding", "для программирования")])
    clientTime = wtforms.RadioField('Сколько времени есть?', default="1-2",
                                    choices=[("1-2", "1-2 часа в неделю"), ("3-5", "3-5 часов в неделю"),
                                             ("5-7", "5-7 часов в неделю"), ("7-10", "7-10 часов в неделю")])


app = Flask(__name__)
csrf = CSRFProtect(app)
SECRET_KEY = secrets.token_urlsafe()
app.config['SECRET_KEY'] = SECRET_KEY


def write_data(data_to_write, data_source):
    with open(data_source, "w") as f:
        json.dump(data_to_write, f, indent=4, ensure_ascii=False)


def load_data(data_source):
    # загрузка данных
    try:
        with open(data_source, 'r') as f:
            result = (json.load(f)).values()
    except FileNotFoundError:
        result = None
    
    return result


def add_list_data(data_to_add, data_source):
    try:
        with open(data_source, 'r') as f:
            records = json.load(f)
    except FileNotFoundError:
        records = []
    
    records.append(data_to_add)
    write_data(records, data_source)


def load_all_data():
    # загрузка данных
    result = load_data(ALL_DATA)
    if result is None:
        from data import goals, teachers
        result = {'goals': goals, 'teachers': teachers}
        write_data(result, ALL_DATA)
        result=result.values()
    
    return result


@app.route('/')
def render_main():
    # Загрузка данных
    goals, teachers = load_all_data()
    
    if len(teachers) > 6:
        random.seed()
        teachers = random.sample(teachers, 6)
    
    return render_template('index.html', goals=goals, teachers=teachers)


@app.route('/goals/<goal>/')
def render_goals_item(goal):
    # Загрузка данных
    goals, teachers = load_all_data()
    
    # Проверки входных данных
    if goal not in goals:
        return render_template('error.html', text="К сожалению, вы ввели неверную цель"), 404
    
    teachers = [t for t in teachers if goal in t["goals"]]
    return render_template('goal.html', goals=goals, teachers=teachers, goal=goal)


@app.route('/profiles/<int:teacher_id>/')
def render_profiles_item(teacher_id):
    # Загрузка данных
    goals, teachers = load_all_data()
    
    teacher = next((t for t in teachers if t["id"] == teacher_id), -1)
    if teacher == -1:
        return render_template('error.html', text="К сожалению, данной страницы не существует"), 404
    
    return render_template('profile.html', t=teacher, goals=goals, weekdays=WEEKDAYS)


@app.route('/request/', methods=['GET', 'POST'])
def render_request():
    form = RequestForm()
    return render_template('request.html', form=form)


@app.route('/request_done/', methods=['POST'])
def render_request_done():
    # Если данные не были отправлены
    if request.method != "POST":
        # Если пользователь попал на эту страницу не из формы ввода, выдаем 404 ошибку
        return render_template('error.html', text="К сожалению, данной страницы не существует"), 404
    
    # Если данные были отправлены
    form = RequestForm()
    if not form.validate_on_submit():
        # отправляем форму назад
        return render_template('request.html', form=form)
    
    # получаем данные
    client_name = form.clientName.data
    client_phone = form.clientPhone.data
    client_goal = form.clientGoal.data
    client_time = form.clientTime.data
    
    goal = next((g[1] for g in form.clientGoal.choices if g[0] == client_goal), -1)
    time = next((t[1] for t in form.clientTime.choices if t[0] == client_time), -1)
    
    if goal == -1 or time == -1:
        return render_template('error.html', text="К сожалению, вы ввели неверные данные"), 404
    
    # сохраняем данные
    add_list_data({'clientName': client_name, 'clientPhone': client_phone, 'clientGoal': goal,
                   'clientTime': time}, REQUEST_DATA)
    
    # переходим на request_done
    return render_template('request_done.html', clientName=client_name, clientPhone=client_phone,
                           clientGoal=goal, clientTime=time)


@app.route('/booking/<int:teacher_id>/<weekday>/<time>/', methods=['GET', 'POST'])
def render_booking_item(teacher_id, weekday, time):
    # Загрузка данных
    goals, teachers = load_all_data()
    
    form = BookingForm()
    if request.method == "POST":
        # если данные post и get отличаются, приводим их к одному виду
        time = form.clientTime.data
        teacher_id = int(form.clientTeacher.data)
        weekday = form.clientWeekday.data
    
    # Проверки входных данных
    if time not in TIME_VALUES:
        return render_template('error.html', text="К сожалению, вы ввели неверное время"), 404
    if weekday not in DAY_VALUES:
        return render_template('error.html', text="К сожалению, вы ввели неверный день недели"), 404
    day = next((w for w in WEEKDAYS if w[0] == weekday), -1)  #
    if day == -1:
        return render_template('error.html', text="К сожалению, вы ввели неверный день недели"), 404
    teacher = next((t for t in teachers if t["id"] == teacher_id), -1)
    if teacher == -1:
        return render_template('error.html', text="К сожалению, указанного преподавателя не существует"), 404
        
        # Если данные были отправлены
    if request.method == "POST":
        if form.validate_on_submit():
            # получаем данные
            client_name = form.clientName.data
            client_phone = form.clientPhone.data
            
            if not teacher["free"][weekday][time]:
                return render_template('error.html', text="К сожалению, указанное время занято"), 200
            
            teacher["free"][weekday][time] = False
            
            # сохраняем данные
            write_data({'goals': goals, 'teachers': teachers}, ALL_DATA)
            add_list_data({'clientName': client_name, 'clientPhone': client_phone, 'clientTeacher': teacher_id,
                           'clientWeekday': weekday, 'clientTime': time}, BOOKING_DATA)
            
            # переходим на booking_done
            return render_template('booking_done.html', clientName=client_name, clientPhone=client_phone,
                                   clientWeekday=day, clientTime=time)
    
    # Если данные еще НЕ были отправлены или неверны
    # выводим форму
    form.clientTime.data = time
    form.clientTeacher.data = teacher_id
    form.clientWeekday.data = weekday
    return render_template('booking.html', form=form, t=teacher, weekday=day, time=time)


@app.errorhandler(404)
def render_not_found(error):
    return render_template('error.html', text="Ничего не нашлось!"), 404


@app.errorhandler(500)
def render_server_error(error):
    return render_template('error.html',
                           text="Что-то не так, но мы все починим:\n{}".format(error.original_exception)), 500


if __name__ == '__main__':
    app.run()
