import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import i2c, sensor
from esphome.const import (
    CONF_ID,
    CONF_DISTANCE,
    CONF_UPDATE_INTERVAL,
    DEVICE_CLASS_DISTANCE,
    STATE_CLASS_MEASUREMENT,
    UNIT_MILLIMETER,
)
from esphome import pins

CODEOWNERS = ["@mrtoy-me"]
DEPENDENCIES = ["i2c"]

vl53l1x_ns = cg.esphome_ns.namespace("vl53l1x")

VL53L1XComponent = vl53l1x_ns.class_(
    "VL53L1XComponent", cg.PollingComponent, i2c.I2CDevice
)

DistanceMode = vl53l1x_ns.enum("DistanceMode")

DISTANCE_MODES = {
    "short": DistanceMode.SHORT,
    "medium": DistanceMode.MEDIUM,
    "long": DistanceMode.LONG, 
}

CONF_DISTANCE_MODE = "distance_mode"
CONF_RANGE_STATUS = "range_status"
CONF_TIMING_BUDGET = "timing_budget"
CONF_XSHUT_PIN = "xshut_pin"

def validate_update_interval(config):
    timing_budget = config[CONF_TIMING_BUDGET].total_milliseconds
    if timing_budget < 0:
        raise cv.Invalid("VL53L1X update_interval must be positive")
    if config[CONF_UPDATE_INTERVAL].total_milliseconds < timing_budget:
        raise cv.Invalid(
            "VL53L1X update_interval must be greater than timing budget"
        )
    return config

CONFIG_SCHEMA = cv.All(
    cv.Schema(   
        {
            cv.GenerateID(): cv.declare_id(VL53L1XComponent),
            cv.Optional(CONF_DISTANCE_MODE, default="long"): cv.enum(
                DISTANCE_MODES, upper=False
            ),
            cv.Optional(CONF_TIMING_BUDGET, default="500ms"): cv.time_period_str_unit,
            cv.Optional(CONF_DISTANCE): sensor.sensor_schema(
                unit_of_measurement=UNIT_MILLIMETER,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_DISTANCE,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_RANGE_STATUS): sensor.sensor_schema(
                accuracy_decimals=0,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_XSHUT_PIN): pins.gpio_output_pin_schema,
        }
    )
    .extend(cv.polling_component_schema("60s"))
    .extend(i2c.i2c_device_schema(0x29)),
    validate_update_interval,
)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    if CONF_DISTANCE in config:
        sens = await sensor.new_sensor(config[CONF_DISTANCE])
        cg.add(var.set_distance_sensor(sens))

    if CONF_RANGE_STATUS in config:
        sens = await sensor.new_sensor(config[CONF_RANGE_STATUS])
        cg.add(var.set_range_status_sensor(sens))

    if CONF_XSHUT_PIN in config:
        pin = await cg.gpio_pin_expression(config[CONF_XSHUT_PIN])
        cg.add(var.set_xshut_pin(pin))

    cg.add(var.config_timing_budget(int(config[CONF_TIMING_BUDGET].total_milliseconds)))
    cg.add(var.config_distance_mode(config[CONF_DISTANCE_MODE]))
