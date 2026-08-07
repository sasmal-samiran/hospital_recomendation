class Car:
    count = 0
    def __init__(self):
        Car.count+=1

s1= Car()
s2= Car()
s3= Car()
s4=Car()
s5=Car()

print("Number of objects created: ", Car.count, "OK")

print("Number of objects created: ", Car.count, "KO")
