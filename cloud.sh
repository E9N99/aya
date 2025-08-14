cat <<'EOF'
---------------------------------------
Installing sedthon is in progress..                                                  
---------------------------------------                                                  


                                                  
Copyright (C) 2020-2024 by TepthonArabic@Github, < https://github.com/E9N99 >.
This file is part of < https://github.com/E9N99 > project,
and is released under the "GNU v3.0 License Agreement".
Please see < https://github.com/E9N99/blob/main/LICENSE >
All rights reserved.
EOF

gunicorn app:app --daemon && python -m zelz
