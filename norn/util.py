def parse_debug(unparsed_data, source, reason):
  with open("/tmp/norn_parse_failed", "a+") as f:
    f.write(source)
    f.write("\nCause: " + reason + "\n")
    f.write(80*"-" + "\n")
    f.write(unparsed_data)
    f.write("\n" + 80*"-" + "\n")
