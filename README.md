# RecipeGenie

RecipeGenie is a comprehensive web application designed to manage recipes, offering features for recipe creation, searching, and community interaction. The application utilizes MySQL for structured data storage, Redis for caching and managing user search history, and MongoDB for storing community threads and comments.

## Features

- **Recipe Management**: Create, search, and view recipes with detailed descriptions and ingredients.
- **Search Functionality**: Efficient search with autocomplete and previous searches managed in Redis.
- **Community Interaction**: Users can post comments on threads and reply to other comments.

## Technologies Used

- **MySQL**: Used for structured data storage including user profiles, recipes, and related details.
- **Redis**: Utilized for caching and storing user search history to provide fast retrieval.
- **MongoDB**: Employed for storing community threads and comments in a flexible, document-based format.

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL Server (see [MySQL Installation Guide](https://dev.mysql.com/doc/mysql-installation-excerpt/5.7/en/))
- Redis Server (see [Redis Installation Guide](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/))
- MongoDB Server (see [MongoDB Installation Guide](https://www.mongodb.com/docs/manual/administration/install-community/))
- Node.js (for frontend build tools, if applicable)

### Installation

#### For Unix-based Systems (Linux, macOS)

1. **Clone the repository**

   ```bash
   git clone https://github.com/matthiaslim/recipe-manager.git
   cd recipe-genie
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory of your project and add the following variables:

   ```env
   MYSQL_HOST=localhost
   MYSQL_USER=<user>
   MYSQL_PASSWORD=<password>
   MYSQL_DB=foodDB
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=foodDB
   ```

   Create a `.flaskenv` file in the root directory of your project and add the following variables:

   ```env
   FLASK_APP=app:create_app
   FLASK_ENV=development
   ```

   Replace `username` and `password` with your actual MySQL credentials.

5. **Execute the SQL Script**

   Run the following command to execute the `table.sql` script and initialize your database:

   ```bash
   mysql -u <user> -p < app/data_prep/table.sql
   ```

   You will be prompted to enter your MySQL password. This command sets up the database schema.

6. **Start the Application**

   ```bash
   flask run
   ```

   The application will be available at `http://127.0.0.1:5000`.

#### For Windows

1. **Clone the repository**

   ```cmd
   git clone https://github.com/matthiaslim/recipe-manager.git
   cd recipe-genie
   ```

2. **Create and activate a virtual environment**

   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```cmd
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory of your project and add the following variables:

   ```env
   MYSQL_HOST=localhost
   MYSQL_USER=<user>
   MYSQL_PASSWORD=<password>
   MYSQL_DB=foodDB
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=foodDB
   ```

   Create a `.flaskenv` file in the root directory of your project and add the following variables:

   ```env
   FLASK_APP=app:create_app
   FLASK_ENV=development
   ```

   Replace `username` and `password` with your actual MySQL credentials.

5. **Execute the SQL Script**

   Run the following command to execute the `table.sql` script and initialize your database:

   ```cmd
   mysql -u <user> -p <foodDB> < app\data_prep\table.sql
   ```

   You will be prompted to enter your MySQL password. This command sets up the database schema.

6. **Start the Application**

   ```cmd
   flask run
   ```

   The application will be available at `http://127.0.0.1:5000`.

## Configuration

- **`.env`**: Configure MySQL, Redis, and MongoDB connection strings.
- **`.flaskenv`**: Set the Flask application and environment settings.

## Troubleshooting

- **Internal Server Error**: Check application logs for detailed error messages. Ensure all services (MySQL, Redis, MongoDB) are running and accessible.
- **Search Functionality Issues**: Ensure Redis is properly configured and running.
- **Community Features Issues**: Check MongoDB connections and document structures for proper setup.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
