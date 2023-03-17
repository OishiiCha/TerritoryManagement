import os, csv
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Map, MapHistory, User
from forms import UserForm, AssignForm, CheckInForm, UploadForm, AddMapForm, AddUserForm, ImportForm, RenameMapForm, ImportForm
from werkzeug.utils import secure_filename
from io import StringIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maps.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['PDF_UPLOAD_FOLDER'] = 'pdf_files'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
migrate = Migrate(app, db)

if not os.path.exists(app.config['PDF_UPLOAD_FOLDER']):
    os.makedirs(app.config['PDF_UPLOAD_FOLDER'])

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<User {self.name}>"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        search_query = request.form.get("search_query")
        if search_query:
            try:
                search_id = int(search_query)
                maps = Map.query.filter_by(id=search_id).all()
            except ValueError:
                maps = []
        else:
            maps = Map.query.all()
    else:
        maps = Map.query.all()

    return render_template("index.html", maps=maps)


@app.route('/assign_map/<int:map_id>', methods=['GET', 'POST'])
def assign_map(map_id):
    map_item = Map.query.get(map_id)
    users = User.query.all()
    if request.method == 'POST':
        assigned_user_name = request.form['user']
        map_item.assigned_to = assigned_user_name
        map_item.assigned_date = datetime.utcnow()  # Update the assigned_date with the current timestamp
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('assign_map.html', map_item=map_item, users=users)


@app.route("/check_in_map/<int:map_id>", methods=["GET", "POST"])
def check_in_map(map_id):
    map_item = Map.query.get(map_id)

    if request.method == "POST":
        if map_item.assigned_to and map_item.assigned_date:
            history_item = MapHistory(
                map_id=map_id,
                typecode=map_item.typecode,
                map_number = map_item.map_number,
                area=map_item.area,
                name=map_item.name,
                assigned_to=map_item.assigned_to,
                assigned_date=map_item.assigned_date,
                checked_in_date=datetime.utcnow()
            )
            db.session.add(history_item)
        map_item.checked_out = False
        map_item.assigned_to = None  # Clear the assigned_to attribute
        map_item.assigned_date = None  # Clear the assigned_date attribute
        map_item.checked_in_date = datetime.utcnow()
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("check_in_map.html", map_item=map_item)

@app.route('/upload_pdf/<int:map_id>', methods=['GET', 'POST'])
def upload_pdf(map_id):
    map_item = Map.query.get(map_id)
    form = UploadForm()

    if form.validate_on_submit():
        pdf_file = form.pdf_file.data
        filename = f'{map_item.id}_map.pdf'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(file_path)
        map_item.pdf_file = filename
        db.session.commit()
        flash(f'PDF file for {map_item.name} has been uploaded', 'success')
        return redirect(url_for('index'))

    return render_template('upload_pdf.html', form=form, map_name=map_item.name)

@app.route("/download_pdf/<int:map_id>")
def download_pdf(map_id):
    map_item = Map.query.get(map_id)
    if map_item is None:
        return f"Error: Map with ID {map_id} not found.", 404
    pdf_file = map_item.pdf_file
    return send_from_directory(app.config["UPLOAD_FOLDER"], pdf_file, as_attachment=True)

@app.route('/delete_pdf/<int:map_id>', methods=['POST'])
def delete_pdf(map_id):
    map_item = Map.query.get(map_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], map_item.pdf_file)
    print(f"File path: {file_path}")

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            map_item.pdf_file = None
            db.session.commit()
            flash(f'PDF file for {map_item.name} has been deleted', 'success')
        except Exception as e:
            print(f"Exception: {e}")
            flash(f'Error deleting the PDF file for {map_item.name}: {e}', 'danger')
    else:
        print("File not found")
        flash(f'PDF file for {map_item.name} not found', 'danger')

    return redirect(url_for('index'))

@app.route("/add_map", methods=["GET", "POST"])
def add_map():
    if request.method == "POST":
        typecode = request.form["typecode"]
        map_number = request.form["map_number"]
        area = request.form["area"]
        name = request.form["name"]
        pdf_file = request.files["pdf_file"]
        pdf_filename = None
        if pdf_file:
            pdf_filename = secure_filename(pdf_file.filename)
            pdf_file.save(os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename))

        new_map = Map(typecode=typecode,map_number=map_number,area=area, name=name, pdf_file=pdf_filename)
        db.session.add(new_map)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add_map.html")

@app.route("/rename_map/<int:map_id>", methods=["GET", "POST"])
def rename_map(map_id):
    map_to_rename = Map.query.get_or_404(map_id)
    if request.method == "POST":
        new_typecode = request.form["new_typecode"]
        new_map_number = request.form["new_map_number"]
        new_area = request.form["new_area"]
        new_name = request.form["new_name"]

        map_to_rename.typecode = new_typecode
        map_to_rename.map_number = new_map_number
        map_to_rename.area = new_area
        map_to_rename.name = new_name

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("rename_map.html", map_to_rename=map_to_rename)


@app.route('/user_management', methods=['GET', 'POST'])
def user_management():
    form = UserForm()
    users = User.query.all()  # Query all users from the User model
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data if form.email.data else None

        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user_management'))  # Redirect to 'user_management' instead of 'index'
    return render_template('user_management.html', form=form, users=users)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404, f"User with ID {user_id} not found")

    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        db.session.commit()
        return redirect(url_for('user_management'))

    return render_template('edit_user.html', form=form, user=user)

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('user_management'))



@app.route('/delete_map/<int:map_id>', methods=['POST'])
def delete_map(map_id):
    map_item = db.session.get(Map, map_id)
    if map_item:
        db.session.delete(map_item)
        db.session.commit()
        flash('Map has been deleted', 'success')
    else:
        flash('Map not found', 'danger')
    return redirect(url_for('index'))



@app.route('/import_export', methods=['GET'])
def import_export():
    import_form = ImportForm()
    return render_template('import_export.html', import_form=import_form)

import csv
from io import StringIO

@app.route('/import_data', methods=['POST'])
def import_data():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        file_string = file.read().decode('utf-8')
        csvfile = StringIO(file_string)
        csvreader = csv.DictReader(csvfile)

        for row in csvreader:
            try:
                map_instance = Map(
                    typecode=row['TypeCode'],
                    map_number=row['Number'],
                    area=row['Suffix'],
                    name=row['MapName'],
                    assigned_to=row['AssignedTo'],
                    assigned_date=row['AssignedDate'],
                    checked_in_date=row['CheckedInDate'],
                )
                db.session.add(map_instance)
            except Exception as e:
                print(e)
                flash("Error importing data", "danger")
                break
        else:
            db.session.commit()
            flash("Data imported successfully", "success")
    else:
        flash("Error importing data", "danger")
    return redirect(url_for('import_export'))


@app.route('/export_data', methods=['GET'])
def export_data():
    EXPORT_FILE_EXTENSION = 'csv'
    exported_file_path = 'data.csv'
    
    maps = Map.query.all()
    
    with open(exported_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['TypeCode', 'Number', 'Suffix', 'MapName', 'AssignedTo', 'AssignedDate', 'CheckedInDate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for map_instance in maps:
            writer.writerow({
                'TypeCode': map_instance.typecode,
                'Number': map_instance.map_number,
                'Suffix': map_instance.area,
                'MapName': map_instance.name,
                'AssignedTo': map_instance.assigned_to,
                'AssignedDate': map_instance.assigned_date,
                'CheckedInDate': map_instance.checked_in_date,
            })

    return send_file(exported_file_path, as_attachment=True, attachment_filename=f'data.{EXPORT_FILE_EXTENSION}')



@app.route("/history")
def history():
    history_records = MapHistory.query.all()
    return render_template("history.html", history_records=history_records)


from forms import EditHistoryForm

@app.route('/edit_history/<int:record_id>', methods=['GET', 'POST'])
def edit_history(record_id):
    record = MapHistory.query.get_or_404(record_id)
    form = EditHistoryForm()

    if form.validate_on_submit():
        record.map_id = form.map_id.data
        record.typecode = form.typecode.data
        record.map_number = form.map_number.data
        record.assigned_to = form.assigned_to.data
        record.assigned_date = form.assigned_date.data
        record.checked_in_date = form.checked_in_date.data

        db.session.commit()
        return redirect(url_for('history'))

    form.map_id.data = record.map_id
    form.typecode.data = record.typecode
    form.map_number.data = record.map_number
    form.assigned_to.data = record.assigned_to
    form.assigned_date.data = record.assigned_date
    form.checked_in_date.data = record.checked_in_date

    return render_template('edit_history.html', form=form, record_id=record_id)

@app.route('/delete_history/<int:record_id>')
def delete_history(record_id):
    record = MapHistory.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('history'))


@app.route('/export_history_csv')
def export_history_csv():
    # Query all history records
    history_records = MapHistory.query.all()

    # Define the CSV headers
    csv_headers = ['id', 'map_id', 'typecode', 'map_number',  'area', 'name', 'assigned_to', 'assigned_date', 'checked_in_date']

    # Generate the CSV content
    def generate_csv(csv_output):
        writer = csv.writer(csv_output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(csv_headers)

        for record in history_records:
            writer.writerow([
                record.id,
                record.map_id,
                record.typecode,
                record.map_number,
                record.area,
                record.name,
                record.assigned_to,
                record.assigned_date,
                record.checked_in_date
            ])

    # Create a generator function for streaming the CSV data
    def stream_csv():
        csv_output = StringIO()
        generate_csv(csv_output)
        csv_output.seek(0)
        return csv_output.getvalue()

    # Generate the current date and time string for the filename
    current_datetime_str = datetime.now().strftime('%Y%m%d_%H-%M-%S')

    # Return the response with the CSV content and appropriate headers
    return Response(
        stream_csv(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=Map_History_Export_{current_datetime_str}.csv'
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2134)

