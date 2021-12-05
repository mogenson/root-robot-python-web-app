# use function decorators to register event handlers

# no filter argument will call handler for every event
@robot.on_bump()
async def any_bumps(bumper: Bumper):
    print(f"any_bumps: {bumper}")


# handler will only be called for matching event
@robot.on_bump(filter=Bumper(left=True, right=True))
async def both_bumps(bumper: Bumper):
    print(f"both_bumps: {bumper}")


# named arguments are optional
@robot.on_bump(Bumper(True, False))
async def left_bumps(bumper: Bumper):
    print(f"left_bumps: {bumper}")


# list of colors can be from 1 to 32 in length
# color sensor will be devided into that many zones
@robot.on_color(Color([Color.ANY, Color.BLACK, Color.ANY]))
async def black_in_center(color: Color):
    print(f"black in center: {color}")


@robot.on_light(Light(state=Light.LEFT_BRIGHTER))
async def wink(light: Light):
    print(f"wink: {light}")


@robot.on_touch(
    Touch(front_left=True, front_right=False, back_right=False, back_left=False)
)
async def touched(touch: Touch):
    print(f"touched: {touch}")
