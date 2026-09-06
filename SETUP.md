```bash
mkdir langgraph_builer
cd langgraph_builer

conda create --prefix ./.conda python=3.12 -y
conda activate ./.conda
code .
git init
touch .gitignore
.conda/ 추가

git remote add origin https://github.com/mookyong/agentic-openspec-labs.git
git remote -v
git status
git branch -M main
git status
git config --global user.email "mookyongkim@google.com"
git config --global user.name "mookyongkim"

git switch -c langgraph_builer
git status

git branch --set-upstream-to=origin/main langgraph_builer
git pull --rebase
git add . 
git commit -m "Initial commit"

openspec init
```
