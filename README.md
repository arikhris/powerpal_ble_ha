# PowerPal BLE for Home Assistant

A native Home Assistant integration for PowerPal BLE energy monitors - **no ESP32 required!**

Direct BLE connection from Home Assistant to your PowerPal device for real-time power consumption monitoring.

## Features

✅ **Direct BLE Connection** - No ESP32 or intermediate device needed  
✅ **Real-time Power Monitoring** - Get instant kW readings  
✅ **Automatic Pairing** - Handles authentication automatically  
✅ **HACS Compatible** - One-click installation  
✅ **Local Control** - Everything stays on your Home Assistant  
✅ **Works Everywhere** - Any Bluetooth-capable system (RPi, NUC, etc.)

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click **+ Create Automation**
4. Search for "PowerPal BLE"
5. Install and restart Home Assistant

### Manual Installation

1. Clone this repository
2. Copy `custom_components/powerpal_ble/` to your `config/custom_components/`
3. Restart Home Assistant

## Configuration

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Create Automation**
3. Search for **"PowerPal BLE"**
4. Fill in your device information:
   - **MAC Address**: `DF:5C:55:00:00:00` (find on device sticker)
   - **Pairing Code**: Your 6-digit code
   - **Pulses per kWh**: Usually 1000

## Finding Your Device Information

### MAC Address
- Check the sticker on your PowerPal device
- Use ESPHome BLE Tracker
- Use nRF Connect mobile app
- Check Home Assistant's Bluetooth devices

### Pairing Code
- From your PowerPal setup documentation
- Printed in the Powerpal info pack
- Available in the Powerpal mobile app

### Pulses per kWh
- Check your electricity meter documentation
- Default is usually 1000 pulses per kWh

## Usage

Once configured, you'll have a sensor entity: **`sensor.powerpal_power`**

### Automations Example

```yaml
automation:
  - alias: "High Power Usage Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.powerpal_power
      above: 5
    action:
      - service: notify.mobile_app_iphone
        data:
          message: "High power: {{ states('sensor.powerpal_power') }} kW"
```

### Templates Example

```yaml
template:
  - sensor:
      - name: "Hourly Energy"
        unit_of_measurement: "kWh"
        state: "{{ (states('sensor.powerpal_power') | float(0) / 60) | round(3) }}"
```

## Troubleshooting

### Connection Failed
- Verify MAC address format (lowercase, colon-separated)
- Verify pairing code is exactly 6 digits
- Ensure no other device is connected to PowerPal via Bluetooth
- Check Home Assistant Bluetooth is enabled

### No Data Received
- Verify device is powered on and in range
- Check Home Assistant logs for errors
- Restart the integration from Settings → Devices & Services

### Linux Bluetooth Permissions
```bash
sudo usermod -a -G bluetooth homeassistant
sudo systemctl restart home-assistant
```

## Data Format

PowerPal sends measurement packets with:
- **Timestamp**: Unix time (4 bytes, little-endian)
- **Pulses**: Pulse count (2 bytes, little-endian)
- **Power**: Calculated as `pulses / pulses_per_kwh` in kW

## Supported Devices

- PowerPal Gen 2 and later with BLE capability

## References

- [PowerPal Official](https://powerpal.net)
- [Bleak BLE Documentation](https://bleak.readthedocs.io)
- [Home Assistant Bluetooth](https://www.home-assistant.io/integrations/bluetooth/)
- [Original PowerPal BLE Research](https://github.com/arikhris/powerpal_ble)

## License

MIT License - Free to use and modify

## Support

For issues and questions:
- **GitHub**: https://github.com/arikhris/powerpal_ble_ha
- **Issues**: https://github.com/arikhris/powerpal_ble_ha/issues

---

**Created by:** [@arikhris](https://github.com/arikhris)  
**Version:** 1.0.0  
**Not affiliated with PowerPal Inc.**