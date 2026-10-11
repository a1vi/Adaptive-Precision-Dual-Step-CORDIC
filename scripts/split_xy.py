with open("xy.hex") as f, open("xy_x.hex","w") as fx, open("xy_y.hex","w") as fy:
    for line in f:
        x,y = line.split()
        fx.write(x+"\n")
        fy.write(y+"\n")
print("split done")
