from environs import Env
from cryptography.fernet import Fernet

env = Env()
env.read_env()

PostgreSQL_Connection = 'sqlite:///SocialAnalytics.db'

#Instagram Setting
insta_name = 'neeraj88maurya21'
insta_password = 'Admin@del21'
tables_name = 'instagram'

#facebook setting
facebook_name = 'kartik14062002@yahoo.com'
facebook_password = 'singh@123'
facebook_tables_name = 'facebook'

#twitter setting

# CIPHER_SUITE = Fernet(env('CIPHER_KEY'))
CIPHER_SUITE = Fernet('6ZNuj7enixwTEYLkJ667EJlRAWEqZwtYW4FyI-XvNv8=')

INDEX_FIELDS = ["phrases", "snippet", "keywords", "text"]
INDEX_PATH = r"index_dir"
ALLOWED_EXTENSIONS = set(["pdf", "PDF"])
TOKEN_EXPIRY = 10
ENABLE_CORS = True
DB_FILE = "sqlite:///{}".format("SocialAnalytics.db")
PostgreSQL_Connection = "sqlite:///{}".format("instance/SocialAnalytics.db")
# DB_FILE = "postgresql://{0}:{1}@{2}:{3}".format("postgres", "Aisal1231!",
#                                                     "socio-analytics.c18idnsgufcg.ap-south-1.rds.amazonaws.com", 5432)
DB_SCHEMA = None
PWD_EXPIRE_DAYS = 90
