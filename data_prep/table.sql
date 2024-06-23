CREATE DATABASE IF NOT EXISTS foodDB;
use foodDB;

CREATE TABLE IF NOT EXISTS User
(
    userID   int          NOT NULL AUTO_INCREMENT,
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    PRIMARY KEY (userID)
);
CREATE TABLE IF NOT EXISTS Recipe
(
    recipeID      int          NOT NULL AUTO_INCREMENT,
    recipeName    varchar(255) NOT NULL,
    description   varchar(255),
    instruction   text,
    averageRating float(2)  DEFAULT 0.0,
    ratingCount   int       DEFAULT 0,
    created_by    int,
    created_At    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_At    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (recipeID),
    FOREIGN KEY (created_by) REFERENCES User (userID)
);
CREATE TABLE IF NOT EXISTS Ingredient
(
    ingredientID   int          NOT NULL AUTO_INCREMENT,
    ingredientName varchar(255) NOT NULL,
    PRIMARY KEY (ingredientID)
);
CREATE TABLE IF NOT EXISTS Recipe_Ingredient
(
    recipeID     int          NOT NULL,
    ingredientID int          NOT NULL,
    quantity     int          NOT NULL,
    unit         varchar(255) NOT NULL,
    PRIMARY KEY (recipeID, ingredientID),
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID),
    FOREIGN KEY (ingredientID) REFERENCES Ingredient (ingredientID)
);

CREATE TABLE IF NOT EXISTS Recipe_Direction
(
    recipeID         int          NOT NULL,
    instructionOrder int          NOT NULL,
    instruction      varchar(255) NOT NULL,
    PRIMARY KEY (recipeID, instructionOrder),
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID)
);

CREATE TABLE IF NOT EXISTS Rating
(
    ratingID   int      NOT NULL AUTO_INCREMENT,
    userID     int      NOT NULL,
    recipeID   int      NOT NULL,
    rating     float(2) NOT NULL,
    comment    varchar(255),
    created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (ratingID),
    FOREIGN KEY (userID) REFERENCES User (userID),
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID),
    CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT unique_user_recipe_rating UNIQUE (userID, recipeID)
);
CREATE TABLE IF NOT EXISTS Thread
(
    threadID   int          NOT NULL AUTO_INCREMENT,
    threadName varchar(255) NOT NULL,
    created_by int,
    PRIMARY KEY (threadID),
    FOREIGN KEY (created_by) REFERENCES User (userID)
);
CREATE TABLE IF NOT EXISTS Reply
(
    replyID    int NOT NULL AUTO_INCREMENT,
    threadID   int NOT NULL,
    replyText  varchar(255),
    created_by int,
    PRIMARY KEY (replyID),
    FOREIGN KEY (threadID) REFERENCES Thread (threadID),
    FOREIGN KEY (created_by) REFERENCES User (userID)
);

CREATE VIEW temp_thread_with_replies AS
SELECT t.threadID,
       t.threadName,
       t.created_by     AS thread_created_by,
       COUNT(r.replyID) AS reply_count
FROM Thread t
         LEFT JOIN Reply r ON t.threadID = r.threadID
GROUP BY t.threadID;

DELIMITER //

CREATE TRIGGER after_insert_rating
    AFTER INSERT
    ON Rating
    FOR EACH ROW
BEGIN
    UPDATE Recipe
    SET ratingCount = ratingCount + 1
    WHERE recipeID = NEW.recipeID;

    UPDATE Recipe
    SET averageRating = ((averageRating * (ratingCount - 1) + NEW.rating) / ratingCount)
    WHERE recipeID = NEW.recipeID;
END //

CREATE TRIGGER after_update_rating
    AFTER UPDATE
    ON Rating
    FOR EACH ROW
BEGIN
    UPDATE Recipe
    SET averageRating = ((averageRating * ratingCount - OLD.rating + NEW.rating) / ratingCount)
    WHERE recipeID = NEW.recipeID;
END //

CREATE TRIGGER after_delete_rating
    AFTER DELETE
    ON Rating
    FOR EACH ROW
BEGIN
    DECLARE rating_count INT DEFAULT 0;

    UPDATE Recipe
    SET ratingCount = ratingCount - 1
    WHERE recipeID = OLD.recipeID;

    SET rating_count = (SELECT ratingCount FROM Recipe WHERE recipeID = OLD.recipeID);

    IF rating_count = 0 THEN
        UPDATE Recipe
        SET averageRating = 0.0
        WHERE recipeID = OLD.recipeID;
    ELSE
        UPDATE Recipe
        SET averageRating = ((averageRating * (ratingCount + 1) - OLD.rating) / ratingCount)
        WHERE recipeID = OLD.recipeID;
    END IF;
END //

CREATE TRIGGER prevent_update_average_rating
BEFORE UPDATE ON Recipe
FOR EACH ROW
BEGIN
    IF NEW.averageRating <> OLD.averageRating THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Update to averageRating is not allowed';
    END IF;
END//

DELIMITER ;
