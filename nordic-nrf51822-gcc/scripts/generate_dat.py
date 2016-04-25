#!/usr/bin/python

# genereate .dat and .zip for an application binary
# https://github.com/NordicSemiconductor/nRF-Master-Control-Panel/blob/master/init%20packet%20handling/How%20to%20generate%20the%20INIT%20file%20for%20DFU.pdf


import argparse, sys, zipfile, glob, os

### shamelessly stolen from https://devzone.nordicsemi.com/question/22586/anyone-do-successfully-dfu-ota-for-sdk701-softdevice-s110-v710/
def calc_crc16(binfile):
  crc = 0xFFFF

  for b in binfile:
    crc = (crc >> 8 & 0x00FF) | (crc << 8 & 0xFF00)
    crc = crc ^ b
    crc = crc ^ ( ( crc & 0x00FF) >> 4 )
    crc = crc ^ ( ( crc << 8) << 4)
    crc = crc ^ ( ( crc & 0x00FF) << 4) << 1
  return crc & 0xFFFF

def convert_uint16_to_array(value):
    """ Convert a number into an array of 2 bytes (LSB). """
    return [(value >> 0 & 0xFF), (value >> 8 & 0xFF)]

def _create_init_packet(init_packet, device_type, device_revision, application_version, softdevice, crc):
    first_mask  = 0b0000000000001111
    second_mask = 0b0000000011110000
    third_mask  = 0b0000111100000000
    fourth_mask = 0b1111000000000000

    init_packet = []
    init_packet.extend([first_mask & device_type, second_mask & device_type])
    init_packet.extend([first_mask & device_revision, second_mask & device_revision])
    init_packet.extend([first_mask & application_version, second_mask & application_version, third_mask & application_version, fourth_mask & application_version])
    init_packet.extend([0x01, 0x00])
    init_packet.extend([first_mask & softdevice, second_mask & softdevice])
    init_packet.extend(convert_uint16_to_array(crc))
###

def _create_manifest(bin_file, dat_file, device_type, device_revision, application_version, softdevice, crc):
  manifest = """
  {
    "manifest": {
        "application": {
            "bin_file": "%s",
            "dat_file": "%s",
            "init_packet_data": {
                "application_version": %d,
                "device_revision": %d,
                "device_type": %d,
                "firmware_crc16": %d,
                "softdevice_req": [
                    %d
                ]
            }
        },
        "dfu_version": 0.5
    }
}"""
  return manifest % (bin_file, dat_file, application_version, device_revision, device_type, crc, softdevice)

def main():

  parser = argparse.ArgumentParser(description='generate a .bin.dat file from an input bin file.')
  parser.add_argument ('file', type = str, help = 'The binary to crc')
  parser.add_argument ('--device-type', default=65535, type = int, help = 'The device type')
  parser.add_argument ('--device-revision', default=65535, type = int, help = 'The revision')
  parser.add_argument ('--softdevice', default=65534, type = int, help = 'The softdevice (singular)')
  parser.add_argument ('--application-version', default=4294967295, type = int, help = 'The application version')

  args = parser.parse_args()

  basename = os.path.basename(args.file)
  name = basename.split('.')[0]

  dat_out_name =  name + '.dat'
  manifest_name = 'manifest.json'

  #if were not in the same directory
  if ('/' in args.file) or ('\\' in args.file):
    path = os.path.dirname(args.file)
    archive_name = path + '/' + name + '.zip'
  else:
    archive_name = name + '.zip'

  try:
    bin = open(args.file, 'rb')

  except:
    sys.exit('Could not open %s' % args.file)

  try:
    archive = zipfile.ZipFile( archive_name, 'w')

  except:
    bin.close();
    sys.exit('Could not open/create %s' % archive_name)

  ba = bytearray(bin.read())
  crc = calc_crc16(ba)
  bin.close();

  init_packet = []
  _create_init_packet(init_packet, args.device_type, args.device_revision, args.application_version, args.softdevice, crc)

  manifest = _create_manifest(basename, dat_out_name, args.device_type, args.device_revision, args.application_version, args.softdevice, crc)

  archive.writestr(dat_out_name, buffer(bytearray(init_packet)), zipfile.ZIP_DEFLATED)
  archive.writestr(manifest_name, manifest, zipfile.ZIP_DEFLATED)
  archive.write(args.file, basename, zipfile.ZIP_DEFLATED)
  archive.close()

if __name__ == "__main__":
  main()
