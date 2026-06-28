-- Script de inserción para la tabla PrendaImagen
-- Asegúrate de que la base de datos y la tabla Prenda ya existen antes de ejecutar.
-- Copia los archivos de imagen a RENTSTYLE-BACK-END/app/static/uploads/prendas/.

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `PrendaImagen` (`idImagen`, `idPrenda`, `filename`, `created_at`) VALUES
  (3, 1, 'RentStyle/prendas/vestidoverde', '2026-06-26 22:52:39'),
  (4, 2, 'RentStyle/prendas/vestidonregro', '2026-06-26 22:52:39'),
  (5, 3, 'RentStyle/prendas/vestidoazul', '2026-06-26 22:52:39'),
  (6, 4, 'RentStyle/prendas/vestidorojo', '2026-06-26 22:52:39'),
  (7, 5, 'RentStyle/prendas/vestidodorado', '2026-06-26 22:52:39');

ALTER TABLE `PrendaImagen` AUTO_INCREMENT = 8;

SET FOREIGN_KEY_CHECKS = 1;
