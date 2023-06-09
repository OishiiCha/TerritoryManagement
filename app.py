import os, csv, shutil
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, flash as flask_flash, request, send_from_directory, Response, send_file, Markup
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast, Integer
from flask_migrate import Migrate
from models import db, Map, MapHistory, User
from forms import UserForm, AssignForm, CheckInForm, UploadForm, AddMapForm, AddUserForm, ImportForm, RenameMapForm, ImportForm, EditHistoryForm, UserImportForm, MapHistoryImportForm
from werkzeug.utils import secure_filename
from io import StringIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maps.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
migrate = Migrate(app, db)


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

def generate_filename(prefix):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{timestamp}.csv"
    return filename

def flash(message, category='info', timeout=5000):
    message = Markup(message)
    flask_flash(message, category)


@app.route('/debug')
def debug():
    maps = Map.query.all()
    return render_template('debug.html', maps=maps)


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
        sort_by = request.args.get('sort_by', default='map_number', type=str)
        if sort_by == 'map_number':
            maps = Map.query.order_by(Map.map_number.asc()).all()
        else:
            # Implement other sorting options
            maps = Map.query.order_by(Map.map_number.asc()).all()

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

# PDF Files
@app.route('/upload_pdf/<int:map_id>', methods=['GET', 'POST'])
def upload_pdf(map_id):
    map_item = Map.query.get(map_id)
    form = UploadForm(map_id=map_id)
    print(f"Received map_id: {map_id}")

    if form.validate_on_submit():
        pdf_file = form.pdf_file.data
        filename = f'{map_item.id}.pdf'

        pdf_data = pdf_file.read()
        print(f'Read {len(pdf_data)} bytes from file')
        map_item.pdf_name = filename
        map_item.pdf_data = pdf_data
        db.session.commit()
        print(f'Added PDF file for {map_item.name} with ID {map_item.id} to the database')

        flash(f'PDF file for {map_item.name} has been uploaded', 'success')
        return redirect(url_for('index'))
    else:
        print(f'Form is not valid. Errors: {form.errors}')

    return render_template('upload_pdf.html', form=form, map_name=map_item.name, pdf_uploaded=map_item.pdf_data is not None)

@app.route("/download_pdf/<int:map_id>")
def download_pdf(map_id):
    map_item = Map.query.get(map_id)
    if map_item is None:
        return f"Error: Map with ID {map_id} not found.", 404

    if map_item.pdf_data is None:
        return f"Error: PDF file for map {map_id} not found.", 404

    pdf_data = map_item.pdf_data
    pdf_name = map_item.pdf_name

    response = make_response(pdf_data)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=pdf_name)

    return response


@app.route('/delete_pdf/<int:map_id>', methods=['POST'])
def delete_pdf(map_id):
    map_item = Map.query.get(map_id)
    if map_item is None:
        return f"Error: Map with ID {map_id} not found.", 404

    if map_item.pdf_data is not None:
        try:
            map_item.pdf_data = None
            map_item.pdf_name = None
            db.session.commit()
            flash(f'PDF file for {map_item.name} has been deleted', 'success')
        except Exception as e:
            print(f"Exception: {e}")
            flash(f'Error deleting the PDF file for {map_item.name}: {e}', 'danger')
    else:
        flash(f'PDF entry for {map_item.name} not found in the database', 'danger')

    return redirect(url_for('index'))


# Maps
@app.route("/add_map", methods=["GET", "POST"])
def add_map():
    if request.method == "POST":
        typecode = request.form["typecode"]
        map_number = request.form["map_number"]
        area = request.form["area"]
        name = request.form["name"]
        pdf_file = request.files["pdf_file"]
        pdf_data = pdf_file.read() if pdf_file else None
        pdf_filename = secure_filename(pdf_file.filename) if pdf_file else None
        if pdf_filename:
            pdf_file.save(os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename))

        new_map = Map(typecode=typecode, map_number=map_number, area=area, name=name, pdf_file=pdf_filename, pdf_data=pdf_data)
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
        try:
            user.name = form.name.data
            user.email = form.email.data
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('user_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
            app.logger.error(f'Error updating user: {str(e)}')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in field "{getattr(form, field).label.text}": {error}', 'error')
                app.logger.error(f'Error in field "{getattr(form, field).label.text}": {error}')

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

@app.route("/history")
def history():
    history_records = MapHistory.query.all()
    return render_template("history.html", history_records=history_records)


@app.route('/edit_history/<int:record_id>', methods=['GET', 'POST'])
def edit_history(record_id):
    try:
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

    except Exception as e:
        # Log the error message
        app.logger.error(f"Error occurred: {e}")
        # Return a custom error page with a 500 status code
        return render_template('error.html', message="An error occurred while processing your request."), 500

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

    # Create the import_export_files folder if it doesn't exist
    if not os.path.exists('import_export_files'):
        os.makedirs('import_export_files')

    # Save the file with the specified naming format
    file_name = generate_filename('S13')
    file_path = os.path.join('import_export_files', file_name)

    # Generate the CSV content
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
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

    return send_file(file_path, as_attachment=True, mimetype='text/csv')

@app.route('/import_export', methods=['GET'])
def import_export():
    import_form = ImportForm()
    user_import_form = UserImportForm()
    map_history_import_form = MapHistoryImportForm()
    return render_template('import_export.html', import_form=import_form, user_import_form=user_import_form, map_history_import_form=map_history_import_form)

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
                    name=row['Area']
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
    # Create the import_export_files folder if it doesn't exist
    if not os.path.exists('import_export_files'):
        os.makedirs('import_export_files')

    maps = Map.query.all()

    # Save the file with the specified naming format
    file_name = generate_filename('current_data_export')
    file_path = os.path.join('import_export_files', file_name)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
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

    return send_file(file_path, as_attachment=True, mimetype='text/csv')


@app.route('/import_users', methods=['POST'])
def import_users():
    print("Import users route called")
    form = UserImportForm()
    if form.validate_on_submit():
        try:
            file = form.file.data
            file_string = file.read().decode('utf-8')
            print("File contents:", file_string)
            csvfile = StringIO(file_string)
            csvreader = csv.DictReader(csvfile, fieldnames=['name', 'email'])

            for row in csvreader:
                print(row)
                name = row.get('name', '')
                email = row.get('email', None)
                user_instance = User(name=name, email=email)
                db.session.add(user_instance)

            db.session.commit()

            # Save the import file to the import_export_files folder
            file_name = generate_user_filename('user_import.csv')
            file_path = os.path.join('import_export_files/', file_name)
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                f.write(file_string)

            flash("User data imported successfully", "success")
        except Exception as e:
            print(e)
            flash("Error importing user data", "danger")
    else:
        flash("Error importing user data", "danger")
    return redirect(url_for('import_export'))


@app.route('/import_map_history', methods=['POST'])
def import_map_history():
    form = MapHistoryImportForm()
    if form.validate_on_submit():
        try:
            file = form.file.data
            file_string = file.read().decode('utf-8')
            csvfile = StringIO(file_string)
            csvreader = csv.DictReader(csvfile)

            for row in csvreader:
                typecode = row.get('TypeCode', None)
                map_number = row.get('Number', None)
                area = row.get('Suffix', None)
                checked_in_date = row.get('DateCompleted', None)
                assigned_date = row.get('DateAssigned', None)
                publisher = row.get('Publisher', None)

                if typecode and map_number:
                    map_instance = Map.query.filter_by(typecode=typecode, map_number=map_number).first()
                    if map_instance:
                        map_history_instance = MapHistory(
                            map_id=map_instance.id,
                            typecode=typecode,
                            map_number=map_number,
                            name=map_instance.name,
                            area=area,
                            checked_in_date=datetime.strptime(checked_in_date, "%Y%m%d").date() if checked_in_date else None,
                            assigned_date=datetime.strptime(assigned_date, "%Y%m%d").date() if assigned_date else None,
                            assigned_to=publisher
                        )
                        db.session.add(map_history_instance)
                    else:
                        flash(f"Map not found for TypeCode: {typecode}, Map Number: {map_number}", "warning")

            db.session.commit()
            flash("Map history data imported successfully", "success")

            # Save the CSV file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"map_history_import_{timestamp}.csv"
            file_path = os.path.join("import_export_files", filename)
            with open(file_path, "w") as f:
                f.write(file_string)

        except Exception as e:
            print(e)
            flash("Error importing map history data", "danger")
    else:
        flash("Error importing map history data", "danger")
    return redirect(url_for('import_export'))


@app.route('/backup_db', methods=['POST'])
def backup_db():
    # Get the current date and time
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")

    # Create the backup folder if it doesn't exist
    backup_dir = "db_bk"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Generate the backup file name
    backup_file = f"{backup_dir}/db_bk_{date_str}.db"

    # Copy the database file to the backup folder
    shutil.copy("instance/maps.db", backup_file)

    # Return a success message to the user
    flash("Database backup created successfully.", "success")
    return redirect(url_for('import_export'))
    pass

@app.route('/backup_files')
def show_backup_files():
    backup_dir = 'db_bk'
    backup_files = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.db'):
            backup_files.append(filename)
    return render_template('backup_files.html', backup_files=backup_files)

@app.route('/restore_db', methods=['GET', 'POST'])
def restore_db():
    if request.method == 'POST':
        backup_dir = "db_bk"
        backup_file = request.form['backup_file']
        backup_path = os.path.join(backup_dir, backup_file)
        shutil.copy(backup_path, "instance/maps.db")
        flash(f"Restored database from backup file {backup_file}", "success")
        return redirect(url_for('import_export'))
    else:
        backup_dir = "db_bk"
        backup_files = os.listdir(backup_dir)
        return render_template('database_backup.html', backup_files=backup_files)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2134, debug=True)

