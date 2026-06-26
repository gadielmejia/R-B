-- Script de inserción para la tabla PrendaImagen
-- Asegúrate de que la base de datos y la tabla Prenda ya existen antes de ejecutar.
-- Copia los archivos de imagen a RENTSTYLE-BACK-END/app/static/uploads/prendas/.

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `PrendaImagen` (`idImagen`, `idPrenda`, `filename`, `created_at`) VALUES
  (1, 9, '484fb02153ba4adcaaefb32469cf3248_10a0220cfb4dcd843ac4a72a5f5e8360.jpg', '2026-06-26 21:48:18'),
  (2, 9, '6130cc967b79496db7726c4e5f3dae64_440c9f3ce99e290a384a4567b3484d03.jpg', '2026-06-26 21:48:18'),
  (3, 1, 'vestidoverde_1782502744.jpg', '2026-06-26 22:52:39'),
  (4, 2, 'vestidonregro_1782502744.jpg', '2026-06-26 22:52:39'),
  (5, 3, 'vestidoazul_1782510836.png', '2026-06-26 22:52:39'),
  (6, 4, 'vestidorojo_1782510836.png', '2026-06-26 22:52:39'),
  (7, 5, 'vestidodorado_1782510836.png', '2026-06-26 22:52:39');

ALTER TABLE `PrendaImagen` AUTO_INCREMENT = 8;

SET FOREIGN_KEY_CHECKS = 1;
