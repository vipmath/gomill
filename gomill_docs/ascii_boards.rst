The :mod:`~gomill.ascii_boards` module
--------------------------------------

.. module:: gomill.ascii_boards
   :synopsis: ASCII Go board representation.

The :mod:`!gomill.ascii_boards` module contains functions for producing and
interpreting ASCII diagrams of Go board positions.


.. function:: render_board(board)

   :rtype: string

   Returns an ASCII diagram of the position on the :class:`.Board` *board*.

   The returned string does not end with a newline.

   ::

      >>> b = boards.Board(9)
      >>> b.play(2, 5, 'b')
      >>> b.play(3, 6, 'w')
      >>> print ascii_boards.render_board(b)
      9  .  .  .  .  .  .  .  .  .
      8  .  .  .  .  .  .  .  .  .
      7  .  .  .  .  .  .  .  .  .
      6  .  .  .  .  .  .  .  .  .
      5  .  .  .  .  .  .  .  .  .
      4  .  .  .  .  .  .  o  .  .
      3  .  .  .  .  .  #  .  .  .
      2  .  .  .  .  .  .  .  .  .
      1  .  .  .  .  .  .  .  .  .
         A  B  C  D  E  F  G  H  J

   See also the :script:`show_sgf.py` example script.


.. function:: play_diagram(board, diagram)

   Sets up the position from *diagram* on *board*.

   *diagram* must be a string in the format returned by :func:`render_board`.

   *board* should be an empty :class:`.Board` object, of the right size.

   Raises :exc:`ValueError` if it can't interpret the diagram.