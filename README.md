## Getting Started

### Please note that this is currently in developement and some features don't work currently. However for simple map management it will work. this was designed to be used as a backup in case the current software used fails and for doing territory work when away from a computer.

![Screenshot 2023-03-21 at 22 28 44](https://user-images.githubusercontent.com/86476845/226756306-945b2dd4-c0cd-4bdc-a86f-4a20884de19e.png)
![Screenshot 2023-03-21 at 22 28 57](https://user-images.githubusercontent.com/86476845/226756328-cb8f1a22-2223-4b9e-8343-9ae4cf459c32.png)
![Screenshot 2023-03-21 at 22 29 07](https://user-images.githubusercontent.com/86476845/226756343-69cd0100-a3bf-44fe-aed1-47dfee5ac8e4.png)
![Screenshot 2023-03-21 at 22 29 21](https://user-images.githubusercontent.com/86476845/226756354-ec7f8b0a-ba5d-4f3c-ae72-9b4ba1acbcac.png)



Make sure that you have the latest version of Python3 and Python3-pip installed.

```
git clone https://github.com/OishiiCha/TerritoryManagement.git
cd TerritoryManagement
pip3 install -r requirements.txt
```

Initialise the database

```
export Flask=app.py
flask db init
flask db migrate
flask db upgrade
```

To run the program for testing
```
python3 app.py
```

Then you can visit the webpage with serverip:5511
