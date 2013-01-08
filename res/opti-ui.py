#!/usr/bin/env python

import os

for uiFile in [os.path.join('./', file) for file in os.listdir('./') if file.endswith('.ui')]:
    os.system('vim %s -c "%%g/^\\s*<!--.*-->$/d" -c "%%g/^.*GDK_POINTER_MOTION_MASK.*$/d" -c "%%s/^\\s\\+//" -c "x"' % uiFile)
