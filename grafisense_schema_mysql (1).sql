CREATE DATABASE IF NOT EXISTS grafisense
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE grafisense;

CREATE TABLE profissional (
  id_profissional BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(150) NOT NULL,
  email VARCHAR(254) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  cpf CHAR(11) NULL,
  telefone VARCHAR(20) NULL,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_profissional),
  UNIQUE KEY uk_profissional_email (email),
  UNIQUE KEY uk_profissional_cpf (cpf),
  CONSTRAINT ck_profissional_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0),
  CONSTRAINT ck_profissional_senha CHECK (CHAR_LENGTH(senha_hash) > 0),
  CONSTRAINT ck_profissional_cpf CHECK (cpf IS NULL OR cpf REGEXP '^[0-9]{11}$')
) ENGINE=InnoDB;

CREATE TABLE paciente (
  id_paciente BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(150) NOT NULL,
  cpf CHAR(11) NOT NULL,
  telefone_responsavel VARCHAR(20) NOT NULL,
  email_responsavel VARCHAR(254) NOT NULL,
  id_profissional BIGINT UNSIGNED NOT NULL,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_paciente),
  UNIQUE KEY uk_paciente_profissional_cpf (id_profissional, cpf),
  KEY idx_paciente_profissional_nome (id_profissional, nome),
  CONSTRAINT fk_paciente_profissional FOREIGN KEY (id_profissional)
    REFERENCES profissional (id_profissional) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT ck_paciente_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0),
  CONSTRAINT ck_paciente_cpf CHECK (cpf REGEXP '^[0-9]{11}$'),
  CONSTRAINT ck_paciente_telefone CHECK (CHAR_LENGTH(TRIM(telefone_responsavel)) > 0),
  CONSTRAINT ck_paciente_email CHECK (CHAR_LENGTH(TRIM(email_responsavel)) > 0)
) ENGINE=InnoDB;


CREATE TABLE avaliacao (
  id_avaliacao BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_paciente BIGINT UNSIGNED NOT NULL,
  id_sessao CHAR(36) NOT NULL,
  data_avaliacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tipo_avaliacao ENUM('MAO', 'ESCRITA') NOT NULL,
  origem_arquivo ENUM('CAMERA', 'UPLOAD') NOT NULL,
  arquivo_uri VARCHAR(1024) NOT NULL,
  status_avaliacao ENUM('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'FALHOU')
    NOT NULL DEFAULT 'PENDENTE',
  versao_modelo VARCHAR(100) NULL,
  PRIMARY KEY (id_avaliacao),
  UNIQUE KEY uk_avaliacao_sessao_tipo (id_paciente, id_sessao, tipo_avaliacao),
  KEY idx_avaliacao_paciente_data (id_paciente, data_avaliacao DESC),
  CONSTRAINT fk_avaliacao_paciente FOREIGN KEY (id_paciente)
    REFERENCES paciente (id_paciente) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT ck_avaliacao_sessao CHECK (CHAR_LENGTH(TRIM(id_sessao)) = 36),
  CONSTRAINT ck_avaliacao_uri CHECK (CHAR_LENGTH(TRIM(arquivo_uri)) > 0),
  CONSTRAINT ck_avaliacao_origem CHECK (
    tipo_avaliacao = 'ESCRITA' OR origem_arquivo = 'CAMERA'
  )
) ENGINE=InnoDB;

CREATE TABLE resultado (
  id_resultado BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_avaliacao BIGINT UNSIGNED NOT NULL,
  resultado_posicionamento ENUM('PINCA', 'PALMAR', 'OUTRO', 'INDETERMINADO') NULL,
  resultado_espacamento DECIMAL(5,2) NULL,
  resultado_legibilidade DECIMAL(5,2) NULL,
  resultado_porcentagem DECIMAL(5,2) NOT NULL,
  gerado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_resultado),
  UNIQUE KEY uk_resultado_avaliacao (id_avaliacao),
  CONSTRAINT fk_resultado_avaliacao FOREIGN KEY (id_avaliacao)
    REFERENCES avaliacao (id_avaliacao) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT ck_resultado_espacamento CHECK (
    resultado_espacamento IS NULL OR resultado_espacamento BETWEEN 0 AND 100
  ),
  CONSTRAINT ck_resultado_legibilidade CHECK (
    resultado_legibilidade IS NULL OR resultado_legibilidade BETWEEN 0 AND 100
  ),
  CONSTRAINT ck_resultado_porcentagem CHECK (resultado_porcentagem BETWEEN 0 AND 100)
) ENGINE=InnoDB;


DELIMITER $$
CREATE TRIGGER trg_resultado_validar_insert
BEFORE INSERT ON resultado FOR EACH ROW
BEGIN
  DECLARE modalidade VARCHAR(10);
  SELECT tipo_avaliacao INTO modalidade
  FROM avaliacao WHERE id_avaliacao = NEW.id_avaliacao;
  IF modalidade = 'MAO' AND (
    NEW.resultado_posicionamento IS NULL OR
    NEW.resultado_espacamento IS NOT NULL OR
    NEW.resultado_legibilidade IS NOT NULL
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resultado MAO exige posicionamento e proibe indicadores de escrita';
  ELSEIF modalidade = 'ESCRITA' AND (
    NEW.resultado_posicionamento IS NOT NULL OR
    NEW.resultado_espacamento IS NULL OR
    NEW.resultado_legibilidade IS NULL
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resultado ESCRITA exige espacamento e legibilidade';
  END IF;
END$$

CREATE TRIGGER trg_resultado_validar_update
BEFORE UPDATE ON resultado FOR EACH ROW
BEGIN
  DECLARE modalidade VARCHAR(10);
  SELECT tipo_avaliacao INTO modalidade
  FROM avaliacao WHERE id_avaliacao = NEW.id_avaliacao;
  IF modalidade = 'MAO' AND (
    NEW.resultado_posicionamento IS NULL OR
    NEW.resultado_espacamento IS NOT NULL OR
    NEW.resultado_legibilidade IS NOT NULL
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resultado MAO exige posicionamento e proibe indicadores de escrita';
  ELSEIF modalidade = 'ESCRITA' AND (
    NEW.resultado_posicionamento IS NOT NULL OR
    NEW.resultado_espacamento IS NULL OR
    NEW.resultado_legibilidade IS NULL
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resultado ESCRITA exige espacamento e legibilidade';
  END IF;
END$$

CREATE TRIGGER trg_avaliacao_preservar_tipo
BEFORE UPDATE ON avaliacao FOR EACH ROW
BEGIN
  IF NEW.tipo_avaliacao <> OLD.tipo_avaliacao
     AND EXISTS (SELECT 1 FROM resultado WHERE id_avaliacao = OLD.id_avaliacao) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nao altere a modalidade de uma avaliacao com resultado';
  END IF;
END$$
DELIMITER ;


CREATE VIEW v_historico_paciente AS
SELECT
  a.id_paciente,
  a.id_sessao,
  MAX(a.data_avaliacao) AS data_sessao,
  MAX(CASE WHEN a.tipo_avaliacao = 'MAO' THEN
    r.resultado_posicionamento END) AS posicionamento_mao,
  MAX(CASE WHEN a.tipo_avaliacao = 'MAO' THEN
    r.resultado_porcentagem END) AS media_mao,
  MAX(CASE WHEN a.tipo_avaliacao = 'ESCRITA' THEN
    r.resultado_espacamento END) AS espacamento,
  MAX(CASE WHEN a.tipo_avaliacao = 'ESCRITA' THEN
    r.resultado_legibilidade END) AS legibilidade,
  MAX(CASE WHEN a.tipo_avaliacao = 'ESCRITA' THEN
    r.resultado_porcentagem END) AS media_escrita,
  CASE WHEN COUNT(r.id_resultado) = 2
            AND SUM(a.status_avaliacao = 'CONCLUIDA') = 2
       THEN ROUND(AVG(r.resultado_porcentagem), 2)
       ELSE NULL END AS media_geral
FROM avaliacao a
LEFT JOIN resultado r ON r.id_avaliacao = a.id_avaliacao
GROUP BY a.id_paciente, a.id_sessao;

-- Consulta de exemplo: filtrar sempre pelo profissional autenticado.
-- SELECT h.* FROM v_historico_paciente h
-- JOIN paciente p ON p.id_paciente = h.id_paciente
-- WHERE p.id_profissional = ? AND p.id_paciente = ?
-- ORDER BY h.data_sessao DESC;
