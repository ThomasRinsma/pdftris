PDF_FILE_TEMPLATE = """
%PDF-1.6

% Root
1 0 obj
<<
  /AcroForm <<
    /Fields [ ###FIELD_LIST### ]
  >>
  /Pages <<
    /Count 1
    /Kids [
      16 0 R
    ]
    /Type /Pages
  >>
  /OpenAction 17 0 R
  /Type /Catalog
>>
endobj

%% Annots Page 1 (also used as overall fields list)
21 0 obj
[
  ###FIELD_LIST###
]
endobj

###FIELDS###

%% Page 1
16 0 obj
<<
  /Annots 21 0 R
  /Contents << >>
  /CropBox [
    0.0
    0.0
    612.0
    792.0
  ]
  /MediaBox [
    0.0
    0.0
    612.0
    792.0
  ]
  /Parent 7 0 R
  /Resources <<
  >>
  /Rotate 0
  /Type /Page
>>
endobj

17 0 obj
<<
  /JS 42 0 R
  /S /JavaScript
>>
endobj


42 0 obj
<< >>
stream

// Hacky wrapper to work with a callback instead of a string 
function setInterval(cb, ms) {
	evalStr = "(" + cb.toString() + ")();";
	return app.setInterval(evalStr, ms);
}

// https://gist.github.com/blixt/f17b47c62508be59987b
var rand_seed = Date.now() % 2147483647;
function rand() {
	return rand_seed = rand_seed * 16807 % 2147483647;
}

// nr of unique rotations per piece
var piece_rotations = [1, 2, 2, 2, 4, 4, 4];

// Piece data: [piece_nr * 32 + rot_nr * 8 + brick_nr * 2 + j]
// with rot_nr between 0 and 4
// with the brick number between 0 and 4
// and j == 0 for X coord, j == 1 for Y coord
var piece_data = [
	// square block
	0, 0, -1, 0, -1, -1, 0, -1, 
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0,

	// line block
	0, 0, -2, 0, -1, 0, 1, 0,
	0, 0, 0, 1, 0, -1, 0, -2,
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0,

	// S-block
	0, 0, -1, -1, 0, -1, 1, 0, 
	0, 0, 0, 1, 1, 0, 1, -1, 
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0,

	// Z-block
	0, 0, -1, 0, 0, -1, 1, -1, 
	0, 0, 1, 1, 1, 0, 0, -1, 
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0,

	// L-block
	0, 0, -1, 0, -1, -1, 1, 0, 
	0, 0, 0, 1, 0, -1, 1, -1, 
	0, 0, -1, 0, 1, 0, 1, 1, 
	0, 0, -1, 1, 0, 1, 0, -1, 

	// J-block
	0, 0, -1, 0, 1, 0, 1, -1, 
	0, 0, 0, 1, 0, -1, 1, 1, 
	0, 0, -1, 1, -1, 0, 1, 0, 
	0, 0, 0, 1, 0, -1, -1, -1, 

	// T-block
	0, 0, -1, 0, 0, -1, 1, 0,  
	0, 0, 0, 1, 0, -1, 1, 0, 
	0, 0, -1, 0, 0, 1, 1, 0, 
	0, 0, -1, 0, 0, 1, 0, -1
]

var TICK_INTERVAL = 50;
var GAME_STEP_TIME = 400;

// Globals
var pixel_fields = [];
var field = [];
var score = 0;
var time_ms = 0;
var last_update = 0;
var interval = 0;

// Current piece
var piece_type = rand() % 7;
var piece_x = 0;
var piece_y = 0;
var piece_rot = 0;

function spawn_new_piece() {
	piece_type = rand() % 7;
	piece_x = 4;
	piece_y = 0;
	piece_rot = 0;
}

function set_controls_visibility(state) {
	this.getField("T_input").hidden = !state;
	this.getField("B_left").hidden = !state;
	this.getField("B_right").hidden = !state;
	this.getField("B_down").hidden = !state;
	this.getField("B_rotate").hidden = !state;
}

function game_init() {
	spawn_new_piece();

	// Gather references to pixel field objects
	// and initialize game state
	for (var x = 0; x < ###GRID_WIDTH###; ++x) {
		pixel_fields[x] = [];
		field[x] = [];
		for (var y = 0; y < ###GRID_HEIGHT###; ++y) {
			pixel_fields[x][y] = this.getField(`P_${x}_${y}`);
			field[x][y] = 0;
		}
	}

	last_update = time_ms;
	score = 0;

	// Start timer
	interval = setInterval(game_tick, TICK_INTERVAL);

	// Hide start button
	this.getField("B_start").hidden = true;

	// Show input box and controls
	set_controls_visibility(true);
}

function game_update() {
	if (time_ms - last_update >= GAME_STEP_TIME) {
		lower_piece();
		last_update = time_ms;
	}
}

function game_over() {
	app.clearInterval(interval);
	app.alert(`Game over! Score: ${score}\nRefresh to restart.`);
}

function rotate_piece() {
	piece_rot++;
	if (piece_rot >= piece_rotations[piece_type]) {
		piece_rot = 0;
	}

	// If we're now out of bounds, undo the rotation
	var illegal = false;
	for (var square = 0; square < 4; ++square) {
		var x_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 0];
		var y_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 1];

		var abs_x = piece_x + x_off;
		var abs_y = piece_y + y_off;

		if (abs_x < 0 || abs_y < 0 || abs_x >= ###GRID_WIDTH### || abs_y >= ###GRID_HEIGHT###) {
			illegal = true;
			break;	
		}
	}
	if (illegal) {
		piece_rot--;
		if (piece_rot < 0) {
			piece_rot = piece_rotations[piece_type] - 1;
		}
	}
}

function is_side_collision() {
	for (var square = 0; square < 4; ++square) {
		var x_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 0];
		var y_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 1];

		var abs_x = piece_x + x_off;
		var abs_y = piece_y + y_off;

		// collision with walls
		if (abs_x < 0 || abs_x >= ###GRID_WIDTH###) {
			return true;
		}

		// collision with field blocks
		if (field[abs_x][abs_y]) {
			return true;
		}
	}
	return false;
}

function handle_input(event) {
	switch (event.change) {
		case 'w': rotate_piece(); break;
		case 'a': move_left(); break;
		case 'd': move_right(); break;
		case 's': lower_piece(); break;
	}
}

function move_left() {
	piece_x--;
	if (is_side_collision()) {
		piece_x++;
	}
}

function move_right() {
	piece_x++;
	if (is_side_collision()) {
		piece_x--;
	}
}

function check_for_filled_lines() {
	for (var row = 0; row < ###GRID_HEIGHT###; ++row) {
		var fill_count = 0;
		for (var column = 0; column < ###GRID_WIDTH###; ++column) {
			fill_count += field[column][row];
		}
		if (fill_count == ###GRID_WIDTH###) {
			// increase score
			score++;
			draw_updated_score();

			// remove line (shift down)
			for (var row2 = row; row2 > 0; row2--) {
				for (var column2 = 0; column2 < ###GRID_WIDTH###; ++column2) {
					field[column2][row2] = field[column2][row2-1];
				}
			}

		}
	}
}

function lower_piece() {
	piece_y++;

	var collision = false;
	for (var square = 0; square < 4; ++square) {
		var x_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 0];
		var y_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 1];

		var abs_x = piece_x + x_off;
		var abs_y = piece_y + y_off;

		if (abs_x < 0 || abs_y < 0 || abs_x >= ###GRID_WIDTH### || abs_y >= ###GRID_HEIGHT###) {
			collision = true;
			break;	
		}

		if (abs_y >= ###GRID_HEIGHT### || field[abs_x][abs_y]) {
			collision = true;
			break;
		}
	}

	if (collision) {
		// if at the top, game over
		if (piece_y == 1) {
			game_over();
			return;
		}

		// add to field
		piece_y--;
		for (var square = 0; square < 4; ++square) {
			var x_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 0];
			var y_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 1];

			var abs_x = piece_x + x_off;
			var abs_y = piece_y + y_off;

			if (abs_x < 0 || abs_y < 0 || abs_x >= ###GRID_WIDTH### || abs_y >= ###GRID_HEIGHT###) {
				// TODO: it is out of bounds, we should nudge it inwards?
				continue;
			}

			field[abs_x][abs_y] = true;
		}

		check_for_filled_lines();
		spawn_new_piece();
	}
}

function draw_updated_score() {
	this.getField("T_score").value = `Score: ${score}`;
}

function set_pixel(x, y, state) {
	if (x < 0 || y < 0 || x >= ###GRID_WIDTH### || y >= ###GRID_HEIGHT###) {
		return;
	}
	pixel_fields[x][###GRID_HEIGHT### - 1 - y].hidden = !state;
}

function draw_field() {
	for (var x = 0; x < ###GRID_WIDTH###; ++x) {
		for (var y = 0; y < ###GRID_HEIGHT###; ++y) {
			set_pixel(x, y, field[x][y]);
		}
	}
}

function draw_current_piece() {
	for (var square = 0; square < 4; ++square) {
		var x_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 0];
		var y_off = piece_data[piece_type * 32 + piece_rot * 8 + square * 2 + 1];

		var abs_x = piece_x + x_off;
		var abs_y = piece_y + y_off;

		set_pixel(abs_x, abs_y, 1);
	}
}

function draw() {
	draw_field();
	draw_current_piece();
}

function game_tick() {
	time_ms += TICK_INTERVAL;
	game_update();
	draw();
}

// Hide controls to start with
set_controls_visibility(false);

// Zoom to fit (on FF)
app.execMenuItem("FitPage");

endstream
endobj


18 0 obj
<<
  /JS 43 0 R
  /S /JavaScript
>>
endobj


43 0 obj
<< >>
stream



endstream
endobj

trailer
<<
  /Root 1 0 R
>>

%%EOF
"""

PLAYING_FIELD_OBJ = """
###IDX### obj
<<
  /FT /Btn
  /Ff 1
  /MK <<
    /BG [
      0.8
    ]
    /BC [
      0 0 0
    ]
  >>
  /Border [ 0 0 1 ]
  /P 16 0 R
  /Rect [
    ###RECT###
  ]
  /Subtype /Widget
  /T (playing_field)
  /Type /Annot
>>
endobj
"""

PIXEL_OBJ = """
###IDX### obj
<<
  /FT /Btn
  /Ff 1
  /MK <<
    /BG [
      ###COLOR###
    ]
    /BC [
      0.5 0.5 0.5
    ]
  >>
  /Border [ 0 0 1 ]
  /P 16 0 R
  /Rect [
    ###RECT###
  ]
  /Subtype /Widget
  /T (P_###X###_###Y###)
  /Type /Annot
>>
endobj
"""

BUTTON_AP_STREAM = """
###IDX### obj
<<
  /BBox [ 0.0 0.0 ###WIDTH### ###HEIGHT### ]
  /FormType 1
  /Matrix [ 1.0 0.0 0.0 1.0 0.0 0.0]
  /Resources <<
    /Font <<
      /HeBo 10 0 R
    >>
    /ProcSet [ /PDF /Text ]
  >>
  /Subtype /Form
  /Type /XObject
>>
stream
q
0.75 g
0 0 ###WIDTH### ###HEIGHT### re
f
Q
q
1 1 ###WIDTH### ###HEIGHT### re
W
n
BT
/HeBo 12 Tf
0 g
10 8 Td
(###TEXT###) Tj
ET
Q
endstream
endobj
"""

BUTTON_OBJ = """
###IDX### obj
<<
  /A <<
	  /JS ###SCRIPT_IDX### R
	  /S /JavaScript
	>>
  /AP <<
    /N ###AP_IDX### R
  >>
  /F 4
  /FT /Btn
  /Ff 65536
  /MK <<
    /BG [
      0.75
    ]
    /CA (###LABEL###)
  >>
  /P 16 0 R
  /Rect [
    ###RECT###
  ]
  /Subtype /Widget
  /T (###NAME###)
  /Type /Annot
>>
endobj
"""

TEXT_OBJ = """
###IDX### obj
<<
	/AA <<
		/K <<
			/JS ###SCRIPT_IDX### R
			/S /JavaScript
		>>
	>>
	/F 4
	/FT /Tx
	/MK <<
	>>
	/MaxLen 0
	/P 16 0 R
	/Rect [
		###RECT###
	]
	/Subtype /Widget
	/T (###NAME###)
	/V (###LABEL###)
	/Type /Annot
>>
endobj
"""

STREAM_OBJ = """
###IDX### obj
<< >>
stream
###CONTENT###
endstream
endobj
"""

# p1 = PIXEL_OBJ.replace("###IDX###", "50 0").replace("###COLOR###","1 0 0").replace("###RECT###", "460 700 480 720")

PX_SIZE = 20
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFF_X = 200
GRID_OFF_Y = 350

fields_text = ""
field_indexes = []
obj_idx_ctr = 50

def add_field(field):
	global fields_text, field_indexes, obj_idx_ctr
	fields_text += field
	field_indexes.append(obj_idx_ctr)
	obj_idx_ctr += 1


# Playing field outline
playing_field = PLAYING_FIELD_OBJ
playing_field = playing_field.replace("###IDX###", f"{obj_idx_ctr} 0")
playing_field = playing_field.replace("###RECT###", f"{GRID_OFF_X} {GRID_OFF_Y} {GRID_OFF_X+GRID_WIDTH*PX_SIZE} {GRID_OFF_Y+GRID_HEIGHT*PX_SIZE}")
add_field(playing_field)

for x in range(GRID_WIDTH):
	for y in range(GRID_HEIGHT):
		# Build object
		pixel = PIXEL_OBJ
		pixel = pixel.replace("###IDX###", f"{obj_idx_ctr} 0")
		c = [0, 0, 0]
		pixel = pixel.replace("###COLOR###", f"{c[0]} {c[1]} {c[2]}")
		pixel = pixel.replace("###RECT###", f"{GRID_OFF_X+x*PX_SIZE} {GRID_OFF_Y+y*PX_SIZE} {GRID_OFF_X+x*PX_SIZE+PX_SIZE} {GRID_OFF_Y+y*PX_SIZE+PX_SIZE}")
		pixel = pixel.replace("###X###", f"{x}")
		pixel = pixel.replace("###Y###", f"{y}")

		add_field(pixel)

def add_button(label, name, x, y, width, height, js):
	script = STREAM_OBJ;
	script = script.replace("###IDX###", f"{obj_idx_ctr} 0")
	script = script.replace("###CONTENT###", js)
	add_field(script)

	ap_stream = BUTTON_AP_STREAM;
	ap_stream = ap_stream.replace("###IDX###", f"{obj_idx_ctr} 0")
	ap_stream = ap_stream.replace("###TEXT###", label)
	ap_stream = ap_stream.replace("###WIDTH###", f"{width}")
	ap_stream = ap_stream.replace("###HEIGHT###", f"{height}")
	add_field(ap_stream)

	button = BUTTON_OBJ;
	button = button.replace("###IDX###", f"{obj_idx_ctr} 0")
	button = button.replace("###SCRIPT_IDX###", f"{obj_idx_ctr-2} 0")
	button = button.replace("###AP_IDX###", f"{obj_idx_ctr-1} 0")
	#button = button.replace("###LABEL###", label)
	button = button.replace("###NAME###", name if name else f"B_{obj_idx_ctr}")
	button = button.replace("###RECT###", f"{x} {y} {x + width} {y + height}")
	add_field(button)

def add_text(label, name, x, y, width, height, js):
	script = STREAM_OBJ;
	script = script.replace("###IDX###", f"{obj_idx_ctr} 0")
	script = script.replace("###CONTENT###", js)
	add_field(script)

	text = TEXT_OBJ;
	text = text.replace("###IDX###", f"{obj_idx_ctr} 0")
	text = text.replace("###SCRIPT_IDX###", f"{obj_idx_ctr-1} 0")
	text = text.replace("###LABEL###", label)
	text = text.replace("###NAME###", name)
	text = text.replace("###RECT###", f"{x} {y} {x + width} {y + height}")
	add_field(text)


add_button("<", "B_left", GRID_OFF_X + 0, GRID_OFF_Y - 70, 50, 50, "move_left();")
add_button(">", "B_right", GRID_OFF_X + 60, GRID_OFF_Y - 70, 50, 50, "move_right();")
add_button("\\\\/", "B_down", GRID_OFF_X + 30, GRID_OFF_Y - 130, 50, 50, "lower_piece();")
add_button("SPIN", "B_rotate", GRID_OFF_X + 140, GRID_OFF_Y - 70, 50, 50, "rotate_piece();")

add_button("Start game", "B_start", GRID_OFF_X + (GRID_WIDTH*PX_SIZE)/2-50, GRID_OFF_Y + (GRID_HEIGHT*PX_SIZE)/2-50, 100, 100, "game_init();")


add_text("Type here for keyboard controls (WASD)", "T_input", GRID_OFF_X + 0, GRID_OFF_Y - 200, GRID_WIDTH*PX_SIZE, 50, "handle_input(event);")

add_text("Score: 0", "T_score", GRID_OFF_X + GRID_WIDTH*PX_SIZE+10, GRID_OFF_Y + GRID_HEIGHT*PX_SIZE-50, 100, 50, "")

filled_pdf = PDF_FILE_TEMPLATE.replace("###FIELDS###", fields_text)
filled_pdf = filled_pdf.replace("###FIELD_LIST###", " ".join([f"{i} 0 R" for i in field_indexes]))
filled_pdf = filled_pdf.replace("###GRID_WIDTH###", f"{GRID_WIDTH}")
filled_pdf = filled_pdf.replace("###GRID_HEIGHT###", f"{GRID_HEIGHT}")

pdffile = open("out.pdf","w")
pdffile.write(filled_pdf)
pdffile.close()