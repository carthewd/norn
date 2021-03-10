import json 
import re

from norn import flags


def parse_debug(unparsed_data, source, reason):
  log_message = """
  {}
  Cause: {}
  -----------------------------------------
  {}
  =========================================
  """.format(source, reason, unparsed_data)

  with open("/tmp/norn_parse_failed", "a+") as f:
    f.write(log_message)


def fix_json(error, broken_json, source):
  '''
  This is a messy hack to try and deal with malformed JSON in the AWS docs, need to find a better way
  '''
  control_chars = ["[", "]", "{", "}"]
  json_list = broken_json.split("\n")
  try:
    for i in range(0, (len(json_list)-1)):
      json_list[i] = re.sub("^\s+", "", json_list[i])
      if i+1 < (len(json_list)):
        if json_list[i+1] != "" and json_list[i+1][0] not in control_chars and json_list[i][-1:] not in control_chars:
          if json_list[i][-1:] != "," and json_list[i+1][-1:] not in control_chars:
            if json_list[i+1] != "  ]," and json_list[i+1] != "   ]," and json_list[i+1] != "],":
              json_list[i] = json_list[i] + ","
          elif json_list[i][-1:] == "," and re.sub("^\s+", "", json_list[i+1])[:1] in control_chars:
            json_list[i] = json_list[i][:-1]
    fixed_json = json.loads(''.join(json_list))
    return fixed_json
  except Exception as e:
    if flags.debug and "(char 0)" not in str(error):
      parse_debug(broken_json, source, str(e))
    pass
