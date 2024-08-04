CREATE DATABASE IF NOT EXISTS foodDB;
USE foodDB;

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
    description   text,
    averageRating float(2)     DEFAULT 0.0,
    ratingCount   int          DEFAULT 0,
    created_by    int,
    created_At    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_At    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID) ON DELETE CASCADE,
    FOREIGN KEY (ingredientID) REFERENCES Ingredient (ingredientID)
);

CREATE TABLE IF NOT EXISTS Recipe_Direction
(
    recipeID         int          NOT NULL,
    instructionOrder int          NOT NULL,
    instruction      text         NOT NULL,
    PRIMARY KEY (recipeID, instructionOrder),
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID) ON DELETE CASCADE
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
    FOREIGN KEY (recipeID) REFERENCES Recipe (recipeID) ON DELETE CASCADE,
    CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT unique_user_recipe_rating UNIQUE (userID, recipeID)
);

DELIMITER //

CREATE TRIGGER after_insert_rating
    AFTER INSERT
    ON Rating
    FOR EACH ROW
BEGIN
    DECLARE rating_count INT;

    UPDATE Recipe
    SET ratingCount = ratingCount + 1
    WHERE recipeID = NEW.recipeID;

    SELECT ratingCount INTO rating_count FROM Recipe WHERE recipeID = NEW.recipeID;
    SET @allow_trigger_update = TRUE;

    UPDATE Recipe
    SET averageRating = ((averageRating * (rating_count - 1) + NEW.rating) / rating_count)
    WHERE recipeID = NEW.recipeID;

    SET @allow_trigger_update = FALSE;
END //

CREATE TRIGGER after_update_rating
    AFTER UPDATE
    ON Rating
    FOR EACH ROW
BEGIN
    DECLARE rating_count INT;

    SELECT ratingCount INTO rating_count FROM Recipe WHERE recipeID = NEW.recipeID;
    SET @allow_trigger_update = TRUE;

    UPDATE Recipe
    SET averageRating = ((averageRating * rating_count - OLD.rating + NEW.rating) / rating_count)
    WHERE recipeID = NEW.recipeID;

    SET @allow_trigger_update = FALSE;
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

    SELECT ratingCount INTO rating_count FROM Recipe WHERE recipeID = OLD.recipeID;
    SET @allow_trigger_update = TRUE;

    IF rating_count = 0 THEN
        UPDATE Recipe
        SET averageRating = 0.0
        WHERE recipeID = OLD.recipeID;
    ELSE
        UPDATE Recipe
        SET averageRating = ((averageRating * (rating_count + 1) - OLD.rating) / rating_count)
        WHERE recipeID = OLD.recipeID;
    END IF;
    SET @allow_trigger_update = FALSE;
END //

CREATE TRIGGER prevent_update_average_rating
BEFORE UPDATE ON Recipe
FOR EACH ROW
BEGIN
    IF @allow_trigger_update IS NULL THEN
        SET @allow_trigger_update = FALSE;
    END IF;

    IF @allow_trigger_update = FALSE AND NEW.averageRating <> OLD.averageRating THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Update to averageRating is not allowed';
    END IF;
END//

DELIMITER ;
