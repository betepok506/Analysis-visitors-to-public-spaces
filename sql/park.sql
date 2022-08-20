--
-- PostgreSQL database dump
--

-- Dumped from database version 14.3 (Debian 14.3-1.pgdg110+1)
-- Dumped by pg_dump version 14.2

-- Started on 2022-06-06 11:20:10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'WIN1251';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 209 (class 1259 OID 16385)
-- Name: age_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.age_groups (
    id integer NOT NULL,
    name text
);


ALTER TABLE public.age_groups OWNER TO postgres;

--
-- TOC entry 210 (class 1259 OID 16390)
-- Name: age_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.age_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.age_groups_id_seq OWNER TO postgres;

--
-- TOC entry 3458 (class 0 OID 0)
-- Dependencies: 210
-- Name: age_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.age_groups_id_seq OWNED BY public.age_groups.id;


--
-- TOC entry 211 (class 1259 OID 16391)
-- Name: bbox_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bbox_types (
    id integer NOT NULL,
    name text
);


ALTER TABLE public.bbox_types OWNER TO postgres;

--
-- TOC entry 212 (class 1259 OID 16396)
-- Name: bbox_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bbox_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bbox_types_id_seq OWNER TO postgres;

--
-- TOC entry 3459 (class 0 OID 0)
-- Dependencies: 212
-- Name: bbox_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bbox_types_id_seq OWNED BY public.bbox_types.id;


--
-- TOC entry 213 (class 1259 OID 16397)
-- Name: bboxes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bboxes (
    id integer NOT NULL,
    cam_id integer NOT NULL,
    l integer NOT NULL,
    r integer NOT NULL,
    t integer NOT NULL,
    b integer NOT NULL,
    ts timestamp without time zone NOT NULL,
    type integer NOT NULL,
    gender integer NOT NULL,
    age integer NOT NULL,
    frame_id integer NOT NULL,
    processed integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.bboxes OWNER TO postgres;

--
-- TOC entry 214 (class 1259 OID 16401)
-- Name: bboxes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bboxes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bboxes_id_seq OWNER TO postgres;

--
-- TOC entry 3460 (class 0 OID 0)
-- Dependencies: 214
-- Name: bboxes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bboxes_id_seq OWNED BY public.bboxes.id;


--
-- TOC entry 215 (class 1259 OID 16402)
-- Name: camera_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.camera_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.camera_id_seq OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 16403)
-- Name: camera; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.camera (
    id integer DEFAULT nextval('public.camera_id_seq'::regclass) NOT NULL,
    fps integer NOT NULL,
    start_ts timestamp without time zone,
    url text,
    max_dist_between_bbox integer,
    min_square_bbox integer,
    cnt_fps_del integer,
    name_cam text,
    cur_frame integer,
    all_frame integer,
    fps_video integer,
    CONSTRAINT camera_name_cam_check CHECK ((name_cam <> ''::text))
);


ALTER TABLE public.camera OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16410)
-- Name: camera_process; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.camera_process (
    id integer NOT NULL,
    queue_in text,
    queue_out text,
    status integer,
    id_header integer,
    queue_callback text,
    cam_id integer,
    queue_analizer_out text,
    queue_analizer_in text
);


ALTER TABLE public.camera_process OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16415)
-- Name: camera_process_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.camera_process_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.camera_process_id_seq OWNER TO postgres;

--
-- TOC entry 3461 (class 0 OID 0)
-- Dependencies: 218
-- Name: camera_process_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.camera_process_id_seq OWNED BY public.camera_process.id;


--
-- TOC entry 219 (class 1259 OID 16416)
-- Name: classifaer_process; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classifaer_process (
    id integer NOT NULL,
    queue_in text,
    queue_out text,
    status integer,
    id_header integer,
    type_classifaer integer
);


ALTER TABLE public.classifaer_process OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16421)
-- Name: classifaer_process_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.classifaer_process_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.classifaer_process_id_seq OWNER TO postgres;

--
-- TOC entry 3462 (class 0 OID 0)
-- Dependencies: 220
-- Name: classifaer_process_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.classifaer_process_id_seq OWNED BY public.classifaer_process.id;


--
-- TOC entry 221 (class 1259 OID 16422)
-- Name: default_params; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.default_params (
    id integer NOT NULL,
    num_frame_delete integer,
    max_dist_between_bbox integer,
    min_square_bbox integer,
    proc_freq integer
);


ALTER TABLE public.default_params OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16425)
-- Name: default_params_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.default_params_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.default_params_id_seq OWNER TO postgres;

--
-- TOC entry 3463 (class 0 OID 0)
-- Dependencies: 222
-- Name: default_params_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.default_params_id_seq OWNED BY public.default_params.id;


--
-- TOC entry 223 (class 1259 OID 16426)
-- Name: detector_process; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detector_process (
    id integer NOT NULL,
    queue_in text,
    queue_out text,
    status integer,
    id_header integer
);


ALTER TABLE public.detector_process OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16431)
-- Name: detector_process_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detector_process_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.detector_process_id_seq OWNER TO postgres;

--
-- TOC entry 3464 (class 0 OID 0)
-- Dependencies: 224
-- Name: detector_process_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detector_process_id_seq OWNED BY public.detector_process.id;


--
-- TOC entry 225 (class 1259 OID 16432)
-- Name: header_process; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.header_process (
    id integer NOT NULL,
    name_header text,
    header_id integer,
    queue_in text,
    queue_out text,
    status integer,
    queue_header text
);


ALTER TABLE public.header_process OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16437)
-- Name: header_process_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.header_process_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.header_process_id_seq OWNER TO postgres;

--
-- TOC entry 3465 (class 0 OID 0)
-- Dependencies: 226
-- Name: header_process_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.header_process_id_seq OWNED BY public.header_process.id;


--
-- TOC entry 227 (class 1259 OID 16438)
-- Name: people; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.people (
    id integer NOT NULL,
    clss integer NOT NULL,
    cam_id integer NOT NULL
);


ALTER TABLE public.people OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16441)
-- Name: people_classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.people_classes (
    id integer NOT NULL,
    age_group integer NOT NULL,
    sex text,
    namr text
);


ALTER TABLE public.people_classes OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16446)
-- Name: people_classes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.people_classes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.people_classes_id_seq OWNER TO postgres;

--
-- TOC entry 3466 (class 0 OID 0)
-- Dependencies: 229
-- Name: people_classes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.people_classes_id_seq OWNED BY public.people_classes.id;


--
-- TOC entry 230 (class 1259 OID 16447)
-- Name: people_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.people_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.people_id_seq OWNER TO postgres;

--
-- TOC entry 3467 (class 0 OID 0)
-- Dependencies: 230
-- Name: people_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.people_id_seq OWNED BY public.people.id;


--
-- TOC entry 231 (class 1259 OID 16448)
-- Name: people_map; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.people_map (
    id integer NOT NULL,
    area_id integer NOT NULL,
    bbox_id integer NOT NULL,
    person_id integer NOT NULL
);


ALTER TABLE public.people_map OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 16451)
-- Name: people_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.people_map_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.people_map_id_seq OWNER TO postgres;

--
-- TOC entry 3468 (class 0 OID 0)
-- Dependencies: 232
-- Name: people_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.people_map_id_seq OWNED BY public.people_map.id;


--
-- TOC entry 233 (class 1259 OID 16452)
-- Name: polygons; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.polygons (
    id integer NOT NULL,
    polygon json,
    area_id integer NOT NULL,
    cam_id integer NOT NULL
);


ALTER TABLE public.polygons OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 16457)
-- Name: polygons_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.polygons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.polygons_id_seq OWNER TO postgres;

--
-- TOC entry 3469 (class 0 OID 0)
-- Dependencies: 234
-- Name: polygons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.polygons_id_seq OWNED BY public.polygons.id;


--
-- TOC entry 235 (class 1259 OID 16458)
-- Name: polygons_map; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.polygons_map (
    id integer NOT NULL,
    polygons text,
    area_id integer
);


ALTER TABLE public.polygons_map OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 16463)
-- Name: polygons_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.polygons_map_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.polygons_map_id_seq OWNER TO postgres;

--
-- TOC entry 3470 (class 0 OID 0)
-- Dependencies: 236
-- Name: polygons_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.polygons_map_id_seq OWNED BY public.polygons_map.id;


--
-- TOC entry 237 (class 1259 OID 16464)
-- Name: video; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.video (
    id integer NOT NULL,
    filename text NOT NULL,
    video_md5 text NOT NULL,
    processed integer NOT NULL
);


ALTER TABLE public.video OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 16469)
-- Name: video_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.video_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.video_id_seq OWNER TO postgres;

--
-- TOC entry 3471 (class 0 OID 0)
-- Dependencies: 238
-- Name: video_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.video_id_seq OWNED BY public.video.id;


--
-- TOC entry 3237 (class 2604 OID 16470)
-- Name: age_groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.age_groups ALTER COLUMN id SET DEFAULT nextval('public.age_groups_id_seq'::regclass);


--
-- TOC entry 3238 (class 2604 OID 16471)
-- Name: bbox_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bbox_types ALTER COLUMN id SET DEFAULT nextval('public.bbox_types_id_seq'::regclass);


--
-- TOC entry 3240 (class 2604 OID 16472)
-- Name: bboxes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bboxes ALTER COLUMN id SET DEFAULT nextval('public.bboxes_id_seq'::regclass);


--
-- TOC entry 3243 (class 2604 OID 16473)
-- Name: camera_process id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.camera_process ALTER COLUMN id SET DEFAULT nextval('public.camera_process_id_seq'::regclass);


--
-- TOC entry 3244 (class 2604 OID 16474)
-- Name: classifaer_process id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classifaer_process ALTER COLUMN id SET DEFAULT nextval('public.classifaer_process_id_seq'::regclass);


--
-- TOC entry 3245 (class 2604 OID 16475)
-- Name: default_params id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.default_params ALTER COLUMN id SET DEFAULT nextval('public.default_params_id_seq'::regclass);


--
-- TOC entry 3246 (class 2604 OID 16476)
-- Name: detector_process id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detector_process ALTER COLUMN id SET DEFAULT nextval('public.detector_process_id_seq'::regclass);


--
-- TOC entry 3247 (class 2604 OID 16477)
-- Name: header_process id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.header_process ALTER COLUMN id SET DEFAULT nextval('public.header_process_id_seq'::regclass);


--
-- TOC entry 3248 (class 2604 OID 16478)
-- Name: people id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people ALTER COLUMN id SET DEFAULT nextval('public.people_id_seq'::regclass);


--
-- TOC entry 3249 (class 2604 OID 16479)
-- Name: people_classes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people_classes ALTER COLUMN id SET DEFAULT nextval('public.people_classes_id_seq'::regclass);


--
-- TOC entry 3250 (class 2604 OID 16480)
-- Name: people_map id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people_map ALTER COLUMN id SET DEFAULT nextval('public.people_map_id_seq'::regclass);


--
-- TOC entry 3251 (class 2604 OID 16481)
-- Name: polygons id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polygons ALTER COLUMN id SET DEFAULT nextval('public.polygons_id_seq'::regclass);


--
-- TOC entry 3252 (class 2604 OID 16482)
-- Name: polygons_map id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polygons_map ALTER COLUMN id SET DEFAULT nextval('public.polygons_map_id_seq'::regclass);


--
-- TOC entry 3253 (class 2604 OID 16483)
-- Name: video id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.video ALTER COLUMN id SET DEFAULT nextval('public.video_id_seq'::regclass);


--
-- TOC entry 3423 (class 0 OID 16385)
-- Dependencies: 209
-- Data for Name: age_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.age_groups (id, name) FROM stdin;
\.


--
-- TOC entry 3425 (class 0 OID 16391)
-- Dependencies: 211
-- Data for Name: bbox_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bbox_types (id, name) FROM stdin;
\.


--
-- TOC entry 3427 (class 0 OID 16397)
-- Dependencies: 213
-- Data for Name: bboxes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bboxes (id, cam_id, l, r, t, b, ts, type, gender, age, frame_id, processed) FROM stdin;
\.


--
-- TOC entry 3430 (class 0 OID 16403)
-- Dependencies: 216
-- Data for Name: camera; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.camera (id, fps, start_ts, url, max_dist_between_bbox, min_square_bbox, cnt_fps_del, name_cam, cur_frame, all_frame, fps_video) FROM stdin;
\.


--
-- TOC entry 3431 (class 0 OID 16410)
-- Dependencies: 217
-- Data for Name: camera_process; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.camera_process (id, queue_in, queue_out, status, id_header, queue_callback, cam_id, queue_analizer_out, queue_analizer_in) FROM stdin;
\.


--
-- TOC entry 3433 (class 0 OID 16416)
-- Dependencies: 219
-- Data for Name: classifaer_process; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.classifaer_process (id, queue_in, queue_out, status, id_header, type_classifaer) FROM stdin;
\.


--
-- TOC entry 3435 (class 0 OID 16422)
-- Dependencies: 221
-- Data for Name: default_params; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.default_params (id, num_frame_delete, max_dist_between_bbox, min_square_bbox, proc_freq) FROM stdin;
1	5	100	500	5
\.


--
-- TOC entry 3437 (class 0 OID 16426)
-- Dependencies: 223
-- Data for Name: detector_process; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detector_process (id, queue_in, queue_out, status, id_header) FROM stdin;
\.


--
-- TOC entry 3439 (class 0 OID 16432)
-- Dependencies: 225
-- Data for Name: header_process; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.header_process (id, name_header, header_id, queue_in, queue_out, status, queue_header) FROM stdin;

\.


--
-- TOC entry 3441 (class 0 OID 16438)
-- Dependencies: 227
-- Data for Name: people; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.people (id, clss, cam_id) FROM stdin;
\.


--
-- TOC entry 3442 (class 0 OID 16441)
-- Dependencies: 228
-- Data for Name: people_classes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.people_classes (id, age_group, sex, namr) FROM stdin;
\.


--
-- TOC entry 3445 (class 0 OID 16448)
-- Dependencies: 231
-- Data for Name: people_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.people_map (id, area_id, bbox_id, person_id) FROM stdin;
\.


--
-- TOC entry 3447 (class 0 OID 16452)
-- Dependencies: 233
-- Data for Name: polygons; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.polygons (id, polygon, area_id, cam_id) FROM stdin;
\.


--
-- TOC entry 3449 (class 0 OID 16458)
-- Dependencies: 235
-- Data for Name: polygons_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.polygons_map (id, polygons, area_id) FROM stdin;
\.


--
-- TOC entry 3451 (class 0 OID 16464)
-- Dependencies: 237
-- Data for Name: video; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.video (id, filename, video_md5, processed) FROM stdin;
\.


--
-- TOC entry 3472 (class 0 OID 0)
-- Dependencies: 210
-- Name: age_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.age_groups_id_seq', 1, false);


--
-- TOC entry 3473 (class 0 OID 0)
-- Dependencies: 212
-- Name: bbox_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bbox_types_id_seq', 1, false);


--
-- TOC entry 3474 (class 0 OID 0)
-- Dependencies: 214
-- Name: bboxes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bboxes_id_seq', 1, false);


--
-- TOC entry 3475 (class 0 OID 0)
-- Dependencies: 215
-- Name: camera_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.camera_id_seq', 1, false);


--
-- TOC entry 3476 (class 0 OID 0)
-- Dependencies: 218
-- Name: camera_process_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.camera_process_id_seq', 1, false);


--
-- TOC entry 3477 (class 0 OID 0)
-- Dependencies: 220
-- Name: classifaer_process_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.classifaer_process_id_seq', 1, false);


--
-- TOC entry 3478 (class 0 OID 0)
-- Dependencies: 222
-- Name: default_params_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.default_params_id_seq', 1, true);


--
-- TOC entry 3479 (class 0 OID 0)
-- Dependencies: 224
-- Name: detector_process_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detector_process_id_seq', 1, false);


--
-- TOC entry 3480 (class 0 OID 0)
-- Dependencies: 226
-- Name: header_process_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.header_process_id_seq', 1, true);


--
-- TOC entry 3481 (class 0 OID 0)
-- Dependencies: 229
-- Name: people_classes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.people_classes_id_seq', 1, false);


--
-- TOC entry 3482 (class 0 OID 0)
-- Dependencies: 230
-- Name: people_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.people_id_seq', 1, false);


--
-- TOC entry 3483 (class 0 OID 0)
-- Dependencies: 232
-- Name: people_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.people_map_id_seq', 1, false);


--
-- TOC entry 3484 (class 0 OID 0)
-- Dependencies: 234
-- Name: polygons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.polygons_id_seq', 1, false);


--
-- TOC entry 3485 (class 0 OID 0)
-- Dependencies: 236
-- Name: polygons_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.polygons_map_id_seq', 1, false);


--
-- TOC entry 3486 (class 0 OID 0)
-- Dependencies: 238
-- Name: video_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.video_id_seq', 1, false);


--
-- TOC entry 3255 (class 2606 OID 16485)
-- Name: age_groups age_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.age_groups
    ADD CONSTRAINT age_groups_pkey PRIMARY KEY (id);


--
-- TOC entry 3257 (class 2606 OID 16487)
-- Name: bbox_types bbox_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bbox_types
    ADD CONSTRAINT bbox_types_pkey PRIMARY KEY (id);


--
-- TOC entry 3259 (class 2606 OID 16489)
-- Name: bboxes bboxes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bboxes
    ADD CONSTRAINT bboxes_pkey PRIMARY KEY (id);


--
-- TOC entry 3261 (class 2606 OID 16491)
-- Name: camera camera_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.camera
    ADD CONSTRAINT camera_pkey PRIMARY KEY (id);


--
-- TOC entry 3263 (class 2606 OID 16493)
-- Name: camera_process camera_process_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.camera_process
    ADD CONSTRAINT camera_process_pkey PRIMARY KEY (id);


--
-- TOC entry 3265 (class 2606 OID 16495)
-- Name: classifaer_process classifaer_process_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classifaer_process
    ADD CONSTRAINT classifaer_process_pkey PRIMARY KEY (id);


--
-- TOC entry 3267 (class 2606 OID 16497)
-- Name: default_params default_params_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.default_params
    ADD CONSTRAINT default_params_pkey PRIMARY KEY (id);


--
-- TOC entry 3269 (class 2606 OID 16499)
-- Name: detector_process detector_process_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detector_process
    ADD CONSTRAINT detector_process_pkey PRIMARY KEY (id);


--
-- TOC entry 3271 (class 2606 OID 16501)
-- Name: header_process header_process_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.header_process
    ADD CONSTRAINT header_process_pkey PRIMARY KEY (id);


--
-- TOC entry 3275 (class 2606 OID 16503)
-- Name: people_classes people_classes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people_classes
    ADD CONSTRAINT people_classes_pkey PRIMARY KEY (id);


--
-- TOC entry 3277 (class 2606 OID 16505)
-- Name: people_map people_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people_map
    ADD CONSTRAINT people_map_pkey PRIMARY KEY (id);


--
-- TOC entry 3273 (class 2606 OID 16507)
-- Name: people people_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT people_pkey PRIMARY KEY (id);


--
-- TOC entry 3281 (class 2606 OID 16509)
-- Name: polygons_map polygons_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polygons_map
    ADD CONSTRAINT polygons_map_pkey PRIMARY KEY (id);


--
-- TOC entry 3279 (class 2606 OID 16511)
-- Name: polygons polygons_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polygons
    ADD CONSTRAINT polygons_pkey PRIMARY KEY (id);


--
-- TOC entry 3283 (class 2606 OID 16513)
-- Name: video video_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.video
    ADD CONSTRAINT video_pkey PRIMARY KEY (video_md5);


-- Completed on 2022-06-06 11:20:10

--
-- PostgreSQL database dump complete
--

