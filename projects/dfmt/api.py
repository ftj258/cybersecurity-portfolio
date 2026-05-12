from sanic import Sanic, response
from inc.exceptions import HashException
from inc.conversions import steps, img_to_xml, hash_query, hashdb_create
from inc.sql_loader import load, hash_lister
from time import strftime, localtime
import inc.extract_bloom as bloom
import inc.A2 as A2
import inc.B as B
import asyncio
import json
import uuid
import os

loop = asyncio.get_event_loop()
app = Sanic()

auth = "123"


def authenticate(fn):
	def new_fn(request):
		if request.headers.get("Authorization") != auth:
			return response.json({
				"success": False,
				"error": "Invalid authorization code"
			}, status=403)

		return fn(request)

	return new_fn




@app.route("/hashdb/create", methods=("POST",))
@authenticate
async def hashdb_create_(request):
	db_name = request.args.get("db_name")

	hashdb_create(db_name)

	return response.json({
		"success": True
	}, status=200)



@app.route("/media/load", methods=("POST",))
@authenticate
async def load_media(request):
	for file_name, file_data in request.files.items():
		file_data = file_data[0]

		db_name = request.args.get("db_name")

		if not db_name:
			return response.json({
				"success": False,
				"error": "Missing db_name request parameter"
			}, status=400)

		nonce = str(uuid.uuid4())

		file_name = f"temp_{nonce}.tmp"
		file_path = f"{os.getcwd()}/{file_name}"

		new_file = open(file_name, "w+")
		new_file.write(str(file_data.body))

		try:
			steps(db_name, self._browse_data["file_path"])
			load(db_name + ".db")
		except HashException as e:
			return response.json({
				"success": False,
				"error": str(e)
			}, status=500)
		else:
			return response.json({
				"success": True
			}, status=200)
		finally:
			# cleanup
			os.system(f"del {file_name}")

		break


@app.route("/media/query", methods=("POST",))
@authenticate
async def query_media(request):
	for file_name, file_data in request.files.items():
		file_data = file_data[0]

		include = request.args.get("include")
		db_name = request.args.get("db_name")

		if not include:
			return response.json({
				"success": False,
				"error": "Missing include request parameter. Must specify one of: 1 and/or 2."
			}, status=400)

		if not db_name:
			return response.json({
				"success": False,
				"error": "Missing db_name request parameter."
			}, status=400)

		options = include.split(",")

		nonce = str(uuid.uuid4())

		file_name = f"temp_{nonce}.tmp"
		file_path = f"{os.getcwd()}/{file_name}"

		new_file = open(file_name, "w+")
		new_file.write(str(file_data.body))

		try:
			total, file_path_xml = hash_query(db_name, file_path)

			json_data = {nonce:{}}

			if "1" in options:
				c1_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
				score1, count1 = A2.compute1(file_path_xml, total)
				json_data[nonce]["compute1"] = {"queried_file": file_path , "score": score1, "unique matched hashes": count1, "total sectors in media": total, "timestamp": c1_time}

			if "2" in options:
				c3_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
				harmonic_means, count3, c2 = A2.compute3(file_path_xml, total)
				json_data[nonce]["compute3"] = {"queried_file": file_path_media, "harmonic_means": harmonic_means, "unique matched hashes": count3, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}

			if json_data[nonce]:
				return response.json({
					"success": True,
					"data": json_data
				}, status=200)
			else:
				return response.json({
					"success": False,
					"error": "Nothing to return."
				}, status=500)

		finally:
			os.system("del scan.txt")
			os.system("del /Q/S comp3.db")
			os.system(f"del {file_name}")

		break



@app.route("/bloom/triage", methods=("POST",))
@authenticate
async def bloom_insert(request):
	sql_db_name = request.args.get("sqlite_db_name")

	if not sql_db_name:
		return response.json({
			"success": False,
			"error": "Missing sqlite_db_name request parameter."
		}, status=400)


	hash_list = hash_lister(sql_db_name)

	for entry in hash_list:
		bloom.insert(entry[0].strip(""), entry[1])

	bloom_data = bloom.extract()

	file_name = strftime("triage_filter_%Y%m%d_%H%M%S_HQ", localtime())
	txt_name = file_name + ".txt"
	md5_name = file_name + ".md5"

	json_data = json.dumps(bloom_data)

	with open(txt_name, "w+") as f:
		f.write(json_data)

	os.system(f"{md5deep64} {txt_name} > {md5_name}")

	return response.json({
		"success": True,
		"data": json_data
	}, status=200)


@app.route("/bloom/import", methods=("POST",))
@authenticate
async def bloom_import(request):
	bloom_names = bloom.bloom_names

	for file_name, file_data in request.files.items():
		file_data = file_data[0]
		include = request.args.get("include")

		if not include:
			return response.json({
				"success": False,
				"error": "Missing include request parameter. Must specify a list of bloom filters."
			}, status=400)

		blooms = include.split(",")

		nonce = str(uuid.uuid4())

		file_name = f"temp_{nonce}.tmp"
		file_path = f"{os.getcwd()}/{file_name}"

		new_file = open(file_name, "w+")
		new_file.write(str(file_data.body))

		try:
			img_to_xml(file_path)
			matched, total, empty, score = B.compute(*blooms)

			json_data = {nonce:{}}

			json_data[nonce] = {"matched": matched, "total": total, "empty": empty, "score": score, "media_file": file_path}

			return response.json({
				"success": True,
				"data": json_data
			}, status=200)


		finally:
			os.system("del scan.txt")
			os.system("del /Q/S comp3.db")
			os.system(f"del {file_name}")

		break


@app.route("/bloom/export")
@authenticate
async def bloom_export(request):
	return response.json(bloom.extract())


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8000)
