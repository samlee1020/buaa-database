rm -rf ./__pycache__ ./entity/__pycache__
zip -r "/Users/samlee/Desktop/数据库代码打包.zip" "README.md" "main.py" "setup.py" "frontend.py" "app.py" "entity" "templates" -x "*._DS_Store" -x "__MACOSX" -x ".DS_Store" 
